"""Normalized findings validation and publication gating for dsl_check."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dsl_manifest import ValidatedManifest
from dsl_primitives import (
    DIGEST,
    FINDING_CODE,
    FINDINGS_SCHEMA,
    PRODUCER_ID,
    REVISION,
    SEMVER,
    STABLE_ID,
    Report,
    is_string,
    resolve_repository_path,
    safe_relative,
    sha256,
    strict_json_loads,
)


@dataclass
class FindingsBinding:
    path: Path
    manifest: ValidatedManifest
    producer: str
    evaluable: bool
    findings: list[dict[str, Any]]


def findings_object(
    value: Any,
    required: set[str],
    label: str,
    report: Report,
    path: Path,
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        report.error("DSL-FINDINGS-001", f"{label} must be an object", path)
        return None
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required)
    if missing:
        report.error(
            "DSL-FINDINGS-001", f"{label} misses fields: {', '.join(missing)}", path
        )
    if unknown:
        report.error(
            "DSL-FINDINGS-001",
            f"{label} has unknown fields: {', '.join(unknown)}",
            path,
        )
    return value


def validate_evidence_reference(
    value: Any,
    index: int,
    root: Path,
    report: Report,
    report_path: Path,
) -> None:
    fields = {"kind", "path", "digest"}
    item = findings_object(value, fields, f"evidence[{index}]", report, report_path)
    if item is None:
        return
    if item.get("kind") not in {"artifact", "receipt", "log", "attestation"}:
        report.error(
            "DSL-FINDINGS-001", f"evidence[{index}].kind is invalid", report_path
        )
    raw_path = safe_relative(
        item.get("path"), f"evidence[{index}].path", report, report_path
    )
    digest = item.get("digest")
    if not isinstance(digest, str) or DIGEST.fullmatch(digest) is None:
        report.error(
            "DSL-FINDINGS-001", f"evidence[{index}].digest is invalid", report_path
        )
    if raw_path is None:
        return
    resolved = resolve_repository_path(
        root, raw_path, f"evidence[{index}].path", report, report_path
    )
    if resolved is None or not resolved.is_file():
        report.error(
            "DSL-FINDINGS-001", f"evidence path does not exist: {raw_path}", raw_path
        )
    elif (
        isinstance(digest, str)
        and DIGEST.fullmatch(digest)
        and sha256(resolved) != digest
    ):
        report.error(
            "DSL-FINDINGS-001", f"evidence digest is stale: {raw_path}", raw_path
        )


def validate_normalized_finding(
    value: Any,
    index: int,
    root: Path,
    manifest: ValidatedManifest,
    report: Report,
    report_path: Path,
) -> dict[str, Any] | None:
    fields = {
        "id",
        "code",
        "severity",
        "security",
        "path",
        "helpPath",
        "message",
        "resolution",
        "evidence",
    }
    item = findings_object(value, fields, f"findings[{index}]", report, report_path)
    if item is None:
        return None
    identifier = item.get("id")
    if not isinstance(identifier, str) or STABLE_ID.fullmatch(identifier) is None:
        report.error(
            "DSL-FINDINGS-001", f"findings[{index}].id is invalid", report_path
        )
    code = item.get("code")
    if not isinstance(code, str) or FINDING_CODE.fullmatch(code) is None:
        report.error(
            "DSL-FINDINGS-001", f"findings[{index}].code is invalid", report_path
        )
        code = "INVALID-CODE"
    severity = item.get("severity")
    if severity not in {"info", "warning", "error", "critical"}:
        report.error(
            "DSL-FINDINGS-001", f"findings[{index}].severity is invalid", report_path
        )
    security = item.get("security")
    if not isinstance(security, bool):
        report.error(
            "DSL-FINDINGS-001",
            f"findings[{index}].security must be boolean",
            report_path,
        )
        security = False
    safe_relative(item.get("path"), f"findings[{index}].path", report, report_path)
    help_path = safe_relative(
        item.get("helpPath"), f"findings[{index}].helpPath", report, report_path
    )
    critical = bool(security) or severity == "critical"
    page_root = "docs/CRITICAL" if critical else "docs/ERROR"
    expected_help = f"{page_root}/{code}.md"
    if help_path != expected_help:
        report.error(
            "DSL-FINDINGS-001",
            f"findings[{index}].helpPath must equal {expected_help}",
            expected_help,
        )
    catalog_name = "criticalCodes" if critical else "errorCodes"
    if code not in manifest.documentation.get(catalog_name, []):
        report.error(
            "DSL-FINDINGS-001",
            f"finding code is absent from documentation.{catalog_name}; add {expected_help}",
            expected_help,
        )
    if not is_string(item.get("message")):
        report.error(
            "DSL-FINDINGS-001",
            f"findings[{index}].message must be non-empty",
            report_path,
        )
    resolution_fields = {"status", "summary", "resolvedAtRevision"}
    resolution = findings_object(
        item.get("resolution"),
        resolution_fields,
        f"findings[{index}].resolution",
        report,
        report_path,
    )
    if resolution is not None:
        status = resolution.get("status")
        summary = resolution.get("summary")
        resolved_revision = resolution.get("resolvedAtRevision")
        if status not in {"open", "resolved"}:
            report.error(
                "DSL-FINDINGS-001",
                f"findings[{index}].resolution.status is invalid",
                report_path,
            )
        if status == "open" and (summary is not None or resolved_revision is not None):
            report.error(
                "DSL-FINDINGS-001",
                f"findings[{index}] open resolution requires null summary and resolvedAtRevision",
                report_path,
            )
        if status == "resolved":
            if not is_string(summary):
                report.error(
                    "DSL-FINDINGS-001",
                    f"findings[{index}] resolved summary is required",
                    report_path,
                )
            if (
                not isinstance(resolved_revision, str)
                or REVISION.fullmatch(resolved_revision) is None
            ):
                report.error(
                    "DSL-FINDINGS-001",
                    f"findings[{index}] resolvedAtRevision must be a Git SHA",
                    report_path,
                )
    evidence = item.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        report.error(
            "DSL-FINDINGS-001",
            f"findings[{index}].evidence must be non-empty",
            report_path,
        )
    else:
        for evidence_index, reference in enumerate(evidence):
            validate_evidence_reference(
                reference, evidence_index, root, report, report_path
            )
    return item


def validate_findings_report(
    report_path: Path,
    root: Path,
    manifests: dict[str, ValidatedManifest],
    expected_revision: str,
) -> tuple[Report, FindingsBinding | None]:
    report = Report()
    if report_path.is_symlink():
        report.error(
            "DSL-FINDINGS-001",
            "findings report must not be a symlink",
            report_path,
        )
        return report, None
    try:
        document = strict_json_loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        report.error(
            "DSL-FINDINGS-001", f"cannot load findings report: {error}", report_path
        )
        return report, None
    fields = {"schema", "producer", "subject", "evaluable", "failureReason", "findings"}
    item = findings_object(document, fields, "findings report", report, report_path)
    if item is None:
        return report, None
    if item.get("schema") != FINDINGS_SCHEMA:
        report.error(
            "DSL-FINDINGS-001", f"schema must equal {FINDINGS_SCHEMA}", report_path
        )

    producer_fields = {"id", "version", "adapter"}
    producer = findings_object(
        item.get("producer"), producer_fields, "producer", report, report_path
    )
    producer_id = ""
    if producer is not None:
        raw_id = producer.get("id")
        if not isinstance(raw_id, str) or PRODUCER_ID.fullmatch(raw_id) is None:
            report.error("DSL-FINDINGS-001", "producer.id is invalid", report_path)
        else:
            producer_id = raw_id
        version = producer.get("version")
        if not isinstance(version, str) or SEMVER.fullmatch(version) is None:
            report.error(
                "DSL-FINDINGS-001",
                "producer.version must use Semantic Versioning",
                report_path,
            )
        if not is_string(producer.get("adapter")):
            report.error(
                "DSL-FINDINGS-001", "producer.adapter must be non-empty", report_path
            )

    subject_fields = {"repository", "revision", "manifest"}
    subject = findings_object(
        item.get("subject"), subject_fields, "subject", report, report_path
    )
    manifest: ValidatedManifest | None = None
    if subject is not None:
        raw_manifest = safe_relative(
            subject.get("manifest"), "subject.manifest", report, report_path
        )
        if raw_manifest is not None:
            manifest = manifests.get(raw_manifest)
            if manifest is None:
                report.error(
                    "DSL-FINDINGS-003",
                    f"subject.manifest is not a loaded manifest: {raw_manifest}",
                    report_path,
                )
        revision = subject.get("revision")
        if not isinstance(revision, str) or REVISION.fullmatch(revision) is None:
            report.error(
                "DSL-FINDINGS-001",
                "subject.revision must be a lowercase Git SHA",
                report_path,
            )
        elif revision != expected_revision:
            report.error(
                "DSL-FINDINGS-003",
                f"subject.revision {revision} does not bind the gated revision {expected_revision}",
                report_path,
            )
        if manifest is not None:
            repository = manifest.document.get("source", {}).get("repository")
            if subject.get("repository") != repository:
                report.error(
                    "DSL-FINDINGS-003",
                    f"subject.repository must equal manifest source.repository: {repository}",
                    report_path,
                )

    evaluable = item.get("evaluable")
    if not isinstance(evaluable, bool):
        report.error("DSL-FINDINGS-001", "evaluable must be boolean", report_path)
        evaluable = False
    failure_reason = item.get("failureReason")
    if evaluable and failure_reason is not None:
        report.error(
            "DSL-FINDINGS-001",
            "evaluable report requires failureReason=null",
            report_path,
        )
    if not evaluable and not is_string(failure_reason):
        report.error(
            "DSL-FINDINGS-001",
            "unevaluable report requires a failureReason",
            report_path,
        )

    normalized: list[dict[str, Any]] = []
    findings = item.get("findings")
    if not isinstance(findings, list):
        report.error("DSL-FINDINGS-001", "findings must be an array", report_path)
    elif manifest is not None:
        ids: set[str] = set()
        for index, raw in enumerate(findings):
            finding = validate_normalized_finding(
                raw, index, root, manifest, report, report_path
            )
            if finding is None:
                continue
            identifier = finding.get("id")
            if isinstance(identifier, str) and identifier in ids:
                report.error(
                    "DSL-FINDINGS-001",
                    f"duplicate finding id: {identifier}",
                    report_path,
                )
            elif isinstance(identifier, str):
                ids.add(identifier)
            normalized.append(finding)
    if manifest is None or not producer_id:
        return report, None
    return report, FindingsBinding(
        report_path, manifest, producer_id, bool(evaluable), normalized
    )


def gate_findings(
    root: Path,
    manifests: list[ValidatedManifest],
    report_paths: list[Path],
    expected_revision: str,
) -> Report:
    report = Report()
    by_path = {
        item.path.resolve().relative_to(root.resolve()).as_posix(): item
        for item in manifests
    }
    bindings: dict[tuple[str, str], FindingsBinding] = {}
    for report_path in report_paths:
        item_report, binding = validate_findings_report(
            report_path, root, by_path, expected_revision
        )
        report.extend(item_report)
        if binding is None:
            continue
        manifest_path = (
            binding.manifest.path.resolve().relative_to(root.resolve()).as_posix()
        )
        key = (manifest_path, binding.producer)
        if key in bindings:
            report.error(
                "DSL-FINDINGS-001",
                f"duplicate report for producer {binding.producer} and manifest {manifest_path}",
                report_path,
            )
        else:
            bindings[key] = binding

    for manifest in manifests:
        manifest_path = manifest.path.resolve().relative_to(root.resolve()).as_posix()
        policy = manifest.finding_policy
        required = set(policy.get("requiredProducers", []))
        security_producers = set(policy.get("securityProducers", []))
        for producer in sorted(required):
            binding = bindings.get((manifest_path, producer))
            if binding is None:
                report.error(
                    "DSL-FINDINGS-002",
                    f"required findings producer has no report: {producer}",
                    manifest_path,
                )
            elif policy.get("requireEvaluable") is True and not binding.evaluable:
                qualifier = "security " if producer in security_producers else ""
                report.error(
                    "DSL-FINDINGS-002",
                    f"required {qualifier}producer is unevaluable: {producer}",
                    binding.path,
                )
        blocking = set(policy.get("blockingSeverities", []))
        for (bound_manifest, _producer), binding in bindings.items():
            if bound_manifest != manifest_path or not binding.evaluable:
                continue
            for finding in binding.findings:
                resolution = finding.get("resolution", {})
                unresolved = resolution.get("status") != "resolved"
                security_block = (
                    policy.get("blockUnresolvedSecurity") is True
                    and finding.get("security") is True
                )
                severity_block = finding.get("severity") in blocking
                if unresolved and (security_block or severity_block):
                    report.error(
                        "DSL-CRITICAL-001",
                        f"unresolved blocking finding {finding.get('id')}: {finding.get('message')}",
                        finding.get("helpPath", manifest_path),
                    )
    return report


def git_revision(root: Path) -> str | None:
    try:
        value = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return value if REVISION.fullmatch(value) else None
