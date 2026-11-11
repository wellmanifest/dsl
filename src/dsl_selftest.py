"""Dependency-free regression self-test suite for dsl_check."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from dsl_findings import gate_findings, validate_findings_report
from dsl_manifest import (
    check_changed_paths,
    discover_manifests,
    git_paths,
    validate_manifest,
)
from dsl_primitives import (
    FINDINGS_SCHEMA,
    MANIFEST_NAME,
    MANIFEST_SCHEMA,
    Report,
    help_page_text,
    safe_relative,
    sha256,
    uri_is_valid,
    write_example_help_pages,
)


def valid_example_document(
    source_digest: str, documentation_digests: dict[str, str]
) -> dict[str, Any]:
    return {
        "$schema": "https://example.test/dsl-manifest.schema.json",
        "schema": MANIFEST_SCHEMA,
        "id": "example.policy.rules",
        "name": "Example policy rules",
        "version": "1.0.0",
        "status": "experimental",
        "purpose": "Self-test policy DSL",
        "domain": "software-governance",
        "owners": [
            {
                "kind": "repository",
                "id": "example/repository",
                "responsibilities": ["semantics", "validation", "compatibility"],
            }
        ],
        "source": {
            "repository": "https://example.test/repository",
            "path": "CONTRIBUTING.md",
            "declaredVersion": "1",
            "canonical": "markdown-embedded",
            "mediaType": "text/markdown",
            "selectors": ["fenced-code:dsl"],
        },
        "ownedPaths": ["CONTRIBUTING.md", MANIFEST_NAME, "docs/**"],
        "artifacts": [
            {
                "path": "CONTRIBUTING.md",
                "role": "normative-source",
                "digest": source_digest,
            },
            *[
                {"path": path, "role": "documentation", "digest": digest}
                for path, digest in sorted(documentation_digests.items())
            ],
        ],
        "namespaces": [{"prefix": "example", "uri": "https://example.test/"}],
        "projections": [],
        "lifecycle": {
            "compatibility": "semver",
            "stability": "experimental",
            "breaking": "major",
            "additive": "minor",
            "fix": "patch",
        },
        "semantics": {
            "effectModel": "declarative-policy",
            "unknownPolicy": "reject",
            "authoritySchema": None,
        },
        "llm": {
            "mode": "none",
            "requestSchemas": [],
            "responseSchemas": [],
            "naturalLanguage": "typed-source-only",
            "sourceSchema": "wellmanifest.dsl/source/v1",
            "decisionProtocol": "none",
            "modelAuthority": "none",
            "strict": True,
        },
        "documentation": {
            "vocabularyKind": "commands",
            "commandRoot": "docs",
            "errorRoot": "docs/ERROR",
            "criticalRoot": "docs/CRITICAL",
            "commands": ["DOCUMENT", "VERSION"],
            "errorCodes": ["DSL-HASH-001"],
            "criticalCodes": ["SECURITY-001"],
        },
        "findingPolicy": {
            "schema": FINDINGS_SCHEMA,
            "requiredProducers": ["subactor.twin-probes"],
            "securityProducers": ["subactor.twin-probes"],
            "blockingSeverities": ["critical"],
            "requireEvaluable": True,
            "blockUnresolvedSecurity": True,
        },
        "publicationPolicy": {
            "declaredTier": "review",
            "deterministic": True,
            "independentReview": True,
            "externalAuthority": False,
            "runtimeIsolation": False,
        },
        "conformance": {
            "levels": ["manifest"],
            "commands": ["python3 check.py"],
            "validExamples": [],
            "invalidExamples": [],
        },
        "mappings": [],
        "standardsLock": {
            "schema": "wellmanifest.standards-lock/v1",
            "entries": [
                {
                    "standard": "wellmanifest.new-project",
                    "version": "1.0.0",
                    "repository": "https://example.test/new-project",
                    "revision": "b" * 40,
                    "contracts": [
                        {
                            "ref": "schema://example.test/new-project/manifest/v1",
                            "digest": "sha256:" + "1" * 64,
                        }
                    ],
                }
            ],
        },
    }


def _check_discovery_boundaries(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="wellmanifest-dsl-discovery-") as temporary:
        root = Path(temporary)
        included = [
            root / MANIFEST_NAME,
            root / "packages" / "example" / MANIFEST_NAME,
            root / "packages" / "worktrees" / MANIFEST_NAME,
            root / ".subactor" / "contracts" / MANIFEST_NAME,
        ]
        excluded = [
            root / ".worktrees" / "ticket-001" / MANIFEST_NAME,
            root / "worktrees" / "ticket-002" / MANIFEST_NAME,
            root / ".subactor" / "recovery" / "snapshot" / MANIFEST_NAME,
            root / ".subactor" / "sessions" / "example" / MANIFEST_NAME,
            root / ".subactor" / "cache" / "checkout" / MANIFEST_NAME,
            root / ".subactor" / "snapshots" / "saved" / MANIFEST_NAME,
            root / ".subactor" / "receipts" / "saved" / MANIFEST_NAME,
            root / ".subactor" / "leases" / "saved" / MANIFEST_NAME,
        ]
        linked = root / "other" / "linked"
        clone = root / "other" / "clone"
        for path in [
            *included,
            *excluded,
            linked / MANIFEST_NAME,
            clone / MANIFEST_NAME,
        ]:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")
        (root / ".git").mkdir()
        (linked / ".git").write_text("gitdir: ../../metadata\n", encoding="utf-8")
        (clone / ".git").mkdir()
        if discover_manifests(root) != sorted(included):
            failures.append(
                "repository discovery crossed a checkout or operational boundary"
            )
        for checkout in [linked, clone, excluded[2].parent]:
            if discover_manifests(checkout) != [checkout / MANIFEST_NAME]:
                failures.append(
                    "explicit nested checkout or snapshot discovery was rejected"
                )


def _check_security_and_modularity(root: Path, failures: list[str]) -> None:
    dup_manifest = root / "duplicate-manifest.json"
    dup_manifest.write_text('{"schema": "a", "schema": "b"}\n', encoding="utf-8")
    dup_report, _ = validate_manifest(dup_manifest, root)
    if not dup_report.has_code("DSL-MANIFEST-001"):
        failures.append("duplicate JSON keys in manifest were not rejected")
    dup_manifest.unlink()

    ctrl_report = Report()
    if safe_relative("docs/DOCUMENT.md\n", "path", ctrl_report, root / MANIFEST_NAME):
        failures.append("control character in relative path was not rejected")

    git_report, _ = git_paths(root, "--output=/tmp/probe", "HEAD", False)
    if not git_report.has_code("DSL-GIT-001"):
        failures.append("git option injection boundary was not rejected")

    if uri_is_valid("https://example.test/bad space") or uri_is_valid("http:"):
        failures.append("malformed URI with whitespace or missing authority passed")

    src_dir = Path(__file__).resolve().parent
    for py_file in sorted(src_dir.glob("*.py")):
        line_count = len(py_file.read_text(encoding="utf-8").splitlines())
        if line_count >= 500:
            failures.append(f"{py_file.name} exceeds 500 lines ({line_count})")


def self_test() -> int:
    failures: list[str] = []
    _check_discovery_boundaries(failures)
    with tempfile.TemporaryDirectory(prefix="wellmanifest-dsl-") as temporary:
        root = Path(temporary)
        _check_security_and_modularity(root, failures)
        source = root / "CONTRIBUTING.md"
        source.write_text(
            "```dsl\nDOCUMENT EXAMPLE\nVERSION 1\n```\n", encoding="utf-8"
        )
        documentation_digests = write_example_help_pages(root)
        manifest_path = root / MANIFEST_NAME
        document = valid_example_document(sha256(source), documentation_digests)
        manifest_path.write_text(
            json.dumps(document, indent=2) + "\n", encoding="utf-8"
        )

        report, manifest = validate_manifest(manifest_path, root)
        if report.failed or manifest is None:
            failures.append("valid manifest was rejected")

        source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        stale, _ = validate_manifest(manifest_path, root)
        if not stale.has_code("DSL-HASH-001"):
            failures.append("stale artifact digest was not rejected")
        document["artifacts"][0]["digest"] = sha256(source)

        invalid_llm = json.loads(json.dumps(document))
        invalid_llm["llm"].update({"mode": "output", "modelAuthority": "none"})
        manifest_path.write_text(
            json.dumps(invalid_llm, indent=2) + "\n", encoding="utf-8"
        )
        llm_report, _ = validate_manifest(manifest_path, root)
        if not llm_report.has_code("DSL-LLM-001"):
            failures.append("invalid LLM boundary was not rejected")

        dsl_decision = json.loads(json.dumps(document))
        dsl_decision["llm"].update(
            {
                "mode": "bidirectional",
                "requestSchemas": ["example.decision-request/v1"],
                "responseSchemas": ["example.decision-response/v1"],
                "naturalLanguage": "forbidden",
                "sourceSchema": None,
                "decisionProtocol": "dsl-input-output",
                "modelAuthority": "propose-only",
            }
        )
        manifest_path.write_text(
            json.dumps(dsl_decision, indent=2) + "\n", encoding="utf-8"
        )
        if validate_manifest(manifest_path, root)[0].failed:
            failures.append("valid DSL decision boundary was rejected")

        nl_decision = json.loads(json.dumps(dsl_decision))
        nl_decision["llm"].update(
            {
                "naturalLanguage": "typed-source-only",
                "sourceSchema": "example.source/v1",
                "decisionProtocol": "nl-to-dsl-input-output",
            }
        )
        manifest_path.write_text(
            json.dumps(nl_decision, indent=2) + "\n", encoding="utf-8"
        )
        if validate_manifest(manifest_path, root)[0].failed:
            failures.append("valid NL-to-DSL decision boundary was rejected")

        invalid_protocol = json.loads(json.dumps(nl_decision))
        invalid_protocol["llm"]["decisionProtocol"] = "dsl-input-output"
        manifest_path.write_text(
            json.dumps(invalid_protocol, indent=2) + "\n", encoding="utf-8"
        )
        if not validate_manifest(manifest_path, root)[0].has_code("DSL-LLM-001"):
            failures.append("mismatched LLM decision protocol was not rejected")

        invalid_tier = json.loads(json.dumps(document))
        invalid_tier["publicationPolicy"]["declaredTier"] = "basic"
        manifest_path.write_text(
            json.dumps(invalid_tier, indent=2) + "\n", encoding="utf-8"
        )
        if not validate_manifest(manifest_path, root)[0].has_code(
            "DSL-PUBLICATION-001"
        ):
            failures.append("understated publication tier was not rejected")

        duplicate_lock = json.loads(json.dumps(document))
        duplicate_lock["standardsLock"]["entries"].append(
            duplicate_lock["standardsLock"]["entries"][0]
        )
        manifest_path.write_text(
            json.dumps(duplicate_lock, indent=2) + "\n", encoding="utf-8"
        )
        if not validate_manifest(manifest_path, root)[0].has_code("DSL-LOCK-001"):
            failures.append("duplicate standards lock pin was not rejected")

        document["source"]["path"] = "../outside.dsl"
        manifest_path.write_text(
            json.dumps(document, indent=2) + "\n", encoding="utf-8"
        )
        if not validate_manifest(manifest_path, root)[0].has_code("DSL-PATH-001"):
            failures.append("repository path escape was not rejected")

        document = valid_example_document(sha256(source), documentation_digests)
        manifest_path.write_text(
            json.dumps(document, indent=2) + "\n", encoding="utf-8"
        )
        valid_report, valid_manifest = validate_manifest(manifest_path, root)
        grammar = root / "grammar" / "example.ebnf"
        grammar.parent.mkdir()
        grammar.write_text("document = 'EXAMPLE';\n", encoding="utf-8")
        ownership = check_changed_paths(
            root, ["grammar/example.ebnf"], [valid_manifest] if valid_manifest else []
        )
        if valid_report.failed or not ownership.has_code("DSL-OWNER-001"):
            failures.append("unclaimed changed DSL artifact was not rejected")

        with tempfile.TemporaryDirectory(
            prefix="wellmanifest-dsl-outside-"
        ) as external:
            outside_manifest = Path(external) / MANIFEST_NAME
            outside_manifest.write_text(json.dumps(document), encoding="utf-8")
            linked_manifest = root / "linked-manifest.json"
            linked_manifest.symlink_to(outside_manifest)
            if not validate_manifest(linked_manifest, root)[0].has_code("DSL-PATH-001"):
                failures.append(
                    "manifest symlink escape was not rejected before reading"
                )
            outside_page = Path(external) / "DOCUMENT.md"
            outside_page.write_text(
                help_page_text("DOCUMENT", "command"), encoding="utf-8"
            )
            command_page = root / "docs" / "DOCUMENT.md"
            backup_page = root / "docs" / "DOCUMENT.bak"
            command_page.rename(backup_page)
            command_page.symlink_to(outside_page)
            if not validate_manifest(manifest_path, root)[0].has_code("DSL-PATH-001"):
                failures.append("help-page symlink escape was not rejected")
            command_page.unlink()
            backup_page.rename(command_page)

        command_page = root / "docs" / "DOCUMENT.md"
        miscased_page = root / "docs" / "document.md"
        command_page.rename(miscased_page)
        if not validate_manifest(manifest_path, root)[0].has_code("DSL-DOC-002"):
            failures.append("miscased command help page was not rejected")
        miscased_page.rename(command_page)

        complete_page = command_page.read_text(encoding="utf-8")
        command_page.write_text(
            "# DOCUMENT\n\n## Purpose\nSelf-test content.\n", encoding="utf-8"
        )
        if not validate_manifest(manifest_path, root)[0].has_code("DSL-DOC-003"):
            failures.append("incomplete command help page was not rejected")
        command_page.write_text(complete_page, encoding="utf-8")

        documentation_digests = {
            path: sha256(root / path) for path in documentation_digests
        }
        document = valid_example_document(sha256(source), documentation_digests)
        manifest_path.write_text(
            json.dumps(document, indent=2) + "\n", encoding="utf-8"
        )
        final_report, final_manifest = validate_manifest(manifest_path, root)
        if final_report.failed or final_manifest is None:
            failures.append("restored manifest and help pages were rejected")
        else:
            evidence_path = root / "evidence" / "twin-probes.log"
            evidence_path.parent.mkdir(parents=True)
            evidence_path.write_text(
                "deterministic security probe evidence\n", encoding="utf-8"
            )
            revision = "a" * 40
            findings_path = root / "findings.json"
            findings_document = {
                "schema": FINDINGS_SCHEMA,
                "producer": {
                    "id": "subactor.twin-probes",
                    "version": "1.0.0",
                    "adapter": "wellmanifest-twin-probes/v1",
                },
                "subject": {
                    "repository": "https://example.test/repository",
                    "revision": revision,
                    "manifest": MANIFEST_NAME,
                },
                "evaluable": True,
                "failureReason": None,
                "findings": [
                    {
                        "id": "security.example.001",
                        "code": "SECURITY-001",
                        "severity": "critical",
                        "security": True,
                        "path": "CONTRIBUTING.md",
                        "helpPath": "docs/CRITICAL/SECURITY-001.md",
                        "message": "Example unresolved security issue",
                        "resolution": {
                            "status": "open",
                            "summary": None,
                            "resolvedAtRevision": None,
                        },
                        "evidence": [
                            {
                                "kind": "log",
                                "path": "evidence/twin-probes.log",
                                "digest": sha256(evidence_path),
                            }
                        ],
                    }
                ],
            }
            findings_path.write_text(
                json.dumps(findings_document, indent=2) + "\n", encoding="utf-8"
            )
            critical_report = gate_findings(
                root, [final_manifest], [findings_path], revision
            )
            if not critical_report.has_code("DSL-CRITICAL-001"):
                failures.append("unresolved critical finding did not block publication")

            symlink_findings = root / "findings-link.json"
            symlink_findings.symlink_to(findings_path)
            sym_report, _ = validate_findings_report(
                symlink_findings, root, {MANIFEST_NAME: final_manifest}, revision
            )
            if not sym_report.has_code("DSL-FINDINGS-001"):
                failures.append("symlinked findings report was not rejected")

            findings_document["findings"][0]["resolution"] = {
                "status": "resolved",
                "summary": "Verified remediation in the gated revision",
                "resolvedAtRevision": revision,
            }
            findings_path.write_text(
                json.dumps(findings_document, indent=2) + "\n", encoding="utf-8"
            )
            if gate_findings(root, [final_manifest], [findings_path], revision).failed:
                failures.append("resolved critical finding was rejected")

            findings_document.update(
                {
                    "evaluable": False,
                    "failureReason": "probe could not evaluate the repository",
                    "findings": [],
                }
            )
            findings_path.write_text(
                json.dumps(findings_document, indent=2) + "\n", encoding="utf-8"
            )
            unevaluable_report = gate_findings(
                root, [final_manifest], [findings_path], revision
            )
            if not unevaluable_report.has_code("DSL-FINDINGS-002"):
                failures.append(
                    "unevaluable required security producer did not block publication"
                )

    if failures:
        for failure in failures:
            print(f"SELFTEST FAIL: {failure}", file=sys.stderr)
        return 1
    print(
        "SELFTEST PASS: manifest, hash, LLM, path, ownership, help-page, "
        "finding-binding, publication-tier, evaluability, and critical-gate cases"
    )
    return 0
