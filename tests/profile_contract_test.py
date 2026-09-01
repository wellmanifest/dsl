#!/usr/bin/env python3
"""Deterministic conformance checks for execution and recovery profiles."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "profiles" / "wellmanifest-profiles.schema.json"
VALID_FIXTURES = ROOT / "examples" / "profiles" / "valid" / "execution-recovery.json"
INVALID_FIXTURES = (
    ROOT / "examples" / "profiles" / "invalid" / "execution-recovery.json"
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def by_schema(documents: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for document in documents:
        grouped[str(document.get("schema"))].append(document)
    return grouped


def dag_findings(
    slices: list[dict[str, Any]], external_ids: set[str] | None = None
) -> set[str]:
    external_ids = external_ids or set()
    identifiers = [str(item["slice_id"]) for item in slices]
    known = set(identifiers)
    findings: set[str] = set()
    if len(known) != len(identifiers):
        findings.add("PROFILE-DAG-DUPLICATE")
    edges: dict[str, list[str]] = {}
    for item in slices:
        identifier = str(item["slice_id"])
        dependencies = [str(value) for value in item["depends_on"]]
        if identifier in dependencies:
            findings.add("PROFILE-DAG-CYCLE")
        if any(
            value not in known and value not in external_ids for value in dependencies
        ):
            findings.add("PROFILE-DAG-UNKNOWN-DEPENDENCY")
        edges[identifier] = [value for value in dependencies if value in known]

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in visiting:
            findings.add("PROFILE-DAG-CYCLE")
            return
        if identifier in visited:
            return
        visiting.add(identifier)
        for dependency in edges.get(identifier, []):
            visit(dependency)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in identifiers:
        visit(identifier)
    return findings


def semantic_findings(documents: list[dict[str, Any]]) -> set[str]:
    grouped = by_schema(documents)
    findings: set[str] = set()
    plan_schema = "wellmanifest.dsl/profile/delivery-plan/v1"
    split_request_schema = "wellmanifest.dsl/profile/task-split-request/v1"
    split_result_schema = "wellmanifest.dsl/profile/task-split-result/v1"
    resume_observation_schema = "wellmanifest.dsl/profile/resume-observation/v1"
    resume_decision_schema = "wellmanifest.dsl/profile/resume-decision/v1"
    remote_observation_schema = "wellmanifest.dsl/profile/remote-binding-observation/v1"
    remote_decision_schema = "wellmanifest.dsl/profile/remote-rebind-decision/v1"
    tool_request_schema = "wellmanifest.dsl/profile/tool-action-request/v1"
    tool_result_schema = "wellmanifest.dsl/profile/tool-action-result/v1"

    plans = grouped.get(plan_schema, [])
    for plan in plans:
        findings.update(dag_findings(plan["slices"]))

    requests = {
        str(item["request_id"]): item for item in grouped.get(split_request_schema, [])
    }
    for result in grouped.get(split_result_schema, []):
        request = requests.get(str(result["request_id"]))
        if request is None:
            findings.add("PROFILE-SPLIT-REQUEST-MISSING")
            continue
        if (request["plan_ref"], request["plan_sha256"]) != (
            result["plan_ref"],
            result["plan_sha256"],
        ):
            findings.add("PROFILE-PLAN-MISMATCH")
        if request["oversized_slice_id"] != result["supersedes_slice_id"]:
            findings.add("PROFILE-SPLIT-SLICE-MISMATCH")
        if (
            request["observed_files"] <= request["limit_files"]
            and request["observed_minutes"] <= request["limit_minutes"]
        ):
            findings.add("PROFILE-SPLIT-NOT-OVERSIZED")
        original_ids = {
            str(item["slice_id"]) for plan in plans for item in plan.get("slices", [])
        }
        replacements = result["replacement_slices"]
        findings.update(dag_findings(replacements, original_ids))
        replacement_ids = {str(item["slice_id"]) for item in replacements}
        rebindings = result["dependency_rebindings"]
        superseded = str(result["supersedes_slice_id"])
        if result["state"] == "proposed" and (
            set(rebindings) != {superseded}
            or str(rebindings.get(superseded)) not in replacement_ids
        ):
            findings.add("PROFILE-SPLIT-REBINDING")

    resume_observations = grouped.get(resume_observation_schema, [])
    resume_decisions = grouped.get(resume_decision_schema, [])
    for observation, decision in zip(resume_observations, resume_decisions):
        if (observation["checkpoint_ref"], observation["checkpoint_sha256"]) != (
            decision["checkpoint_ref"],
            decision["checkpoint_sha256"],
        ):
            findings.add("PROFILE-CHECKPOINT-MISMATCH")

    remote_observations = grouped.get(remote_observation_schema, [])
    remote_decisions = grouped.get(remote_decision_schema, [])
    for observation in remote_observations:
        observed_at = datetime.fromisoformat(
            observation["observed_at"].replace("Z", "+00:00")
        )
        valid_until = datetime.fromisoformat(
            observation["valid_until"].replace("Z", "+00:00")
        )
        if valid_until <= observed_at:
            findings.add("PROFILE-REMOTE-STALE")
    for observation, decision in zip(remote_observations, remote_decisions):
        binding_fields = ("repository_ref", "remote_name", "route_id", "account_ref")
        if any(observation[field] != decision[field] for field in binding_fields):
            findings.add("PROFILE-REMOTE-BINDING-MISMATCH")

    tool_requests = {
        str(item["action_id"]): item for item in grouped.get(tool_request_schema, [])
    }
    for result in grouped.get(tool_result_schema, []):
        request = tool_requests.get(str(result["action_id"]))
        if request is None:
            findings.add("PROFILE-TOOL-REQUEST-MISSING")
        elif request["capability_ref"] != result["capability_ref"]:
            findings.add("PROFILE-CAPABILITY-MISMATCH")

    for document in documents:
        if document.get("authority_granted") is True:
            findings.add("PROFILE-AUTHORITY-GRANTED")
        if "propose_only" in document and document["propose_only"] is not True:
            findings.add("PROFILE-NOT-PROPOSE-ONLY")
        if document.get("credentials_included") is True:
            findings.add("PROFILE-CREDENTIAL-MATERIAL")
        if document.get("credentials_selected") is True:
            findings.add("PROFILE-CREDENTIAL-SELECTION")
    return findings


def validate_documents(
    validator: Draft202012Validator, documents: list[dict[str, Any]]
) -> set[str]:
    if any(list(validator.iter_errors(document)) for document in documents):
        return {"PROFILE-SCHEMA"}
    return semantic_findings(documents)


def main() -> int:
    schema = load(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    valid_documents = load(VALID_FIXTURES)["documents"]
    valid_findings = validate_documents(validator, valid_documents)
    if valid_findings:
        raise SystemExit(f"valid fixtures rejected: {sorted(valid_findings)}")

    invalid_cases = load(INVALID_FIXTURES)["cases"]
    for case in invalid_cases:
        findings = validate_documents(validator, case["documents"])
        if case["expected"] not in findings:
            raise SystemExit(
                f"invalid fixture {case['name']} missed {case['expected']}: "
                f"{sorted(findings)}"
            )

    print(
        "PROFILE CONTRACT PASS: "
        f"{len(valid_documents)} valid documents, {len(invalid_cases)} invalid cases"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
