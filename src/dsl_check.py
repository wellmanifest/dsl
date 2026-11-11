#!/usr/bin/env python3
"""Deterministic conformance gate for wellmanifest DSL manifests."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC_DIR = str(Path(__file__).resolve().parent)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from dsl_findings import (
    FindingsBinding,
    findings_object,
    gate_findings,
    git_revision,
    validate_evidence_reference,
    validate_findings_report,
    validate_normalized_finding,
)
from dsl_manifest import (
    ValidatedManifest,
    _run_git_command,
    check_changed_paths,
    discover_manifests,
    git_paths,
    is_dsl_sensitive,
    load_targets,
    validate_manifest,
)
from dsl_policy import (
    page_has_section_content,
    required_publication_tier,
    validate_documentation,
    validate_finding_policy,
    validate_help_page,
    validate_publication_policy,
    validate_standards_lock,
)
from dsl_primitives import (
    COMMAND_NAME,
    DIGEST,
    DOMAIN,
    FINDING_CODE,
    FINDINGS_SCHEMA,
    HELP_PAGE_SECTIONS,
    MANIFEST_NAME,
    MANIFEST_SCHEMA,
    MEDIA_TYPE,
    PREFIX,
    PRODUCER_ID,
    REVISION,
    SEMVER,
    STABLE_ID,
    Finding,
    Report,
    check_object,
    check_string_list,
    help_page_text,
    is_string,
    matches,
    resolve_repository_path,
    safe_relative,
    sha256,
    strict_json_loads,
    unique,
    uri_is_valid,
    write_example_help_pages,
)
from dsl_sections import (
    validate_artifacts,
    validate_conformance,
    validate_lifecycle,
    validate_llm,
    validate_mappings,
    validate_namespaces,
    validate_owners,
    validate_projections,
    validate_semantics,
    validate_source,
)
from dsl_selftest import (
    self_test,
    valid_example_document,
)

__all__ = [
    "COMMAND_NAME",
    "DIGEST",
    "DOMAIN",
    "FINDINGS_SCHEMA",
    "FINDING_CODE",
    "HELP_PAGE_SECTIONS",
    "MANIFEST_NAME",
    "MANIFEST_SCHEMA",
    "MEDIA_TYPE",
    "PREFIX",
    "PRODUCER_ID",
    "REVISION",
    "SEMVER",
    "STABLE_ID",
    "Finding",
    "FindingsBinding",
    "Report",
    "ValidatedManifest",
    "_run_git_command",
    "check_changed_paths",
    "check_object",
    "check_string_list",
    "command_changes",
    "command_gate",
    "command_standards",
    "command_validate",
    "discover_manifests",
    "findings_object",
    "gate_findings",
    "git_paths",
    "git_revision",
    "help_page_text",
    "is_dsl_sensitive",
    "is_string",
    "load_targets",
    "main",
    "matches",
    "page_has_section_content",
    "parser",
    "required_publication_tier",
    "resolve_repository_path",
    "safe_relative",
    "self_test",
    "sha256",
    "strict_json_loads",
    "unique",
    "uri_is_valid",
    "valid_example_document",
    "validate_artifacts",
    "validate_conformance",
    "validate_documentation",
    "validate_evidence_reference",
    "validate_finding_policy",
    "validate_findings_report",
    "validate_help_page",
    "validate_lifecycle",
    "validate_llm",
    "validate_manifest",
    "validate_mappings",
    "validate_namespaces",
    "validate_normalized_finding",
    "validate_owners",
    "validate_projections",
    "validate_publication_policy",
    "validate_semantics",
    "validate_source",
    "validate_standards_lock",
    "write_example_help_pages",
]


def command_validate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    report, _ = load_targets(args.targets or ["."], root)
    print(report.render(args.format))
    return 1 if report.failed else 0


def command_changes(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    report, manifests = load_targets(["."], root)
    changed: set[str] = set()
    if args.changed_file:
        for index, raw in enumerate(args.changed_file):
            normalized = safe_relative(
                raw, f"changed-file[{index}]", report, root / MANIFEST_NAME
            )
            if normalized is not None:
                changed.add(normalized)
    elif args.base:
        git_report, changed = git_paths(
            root, args.base, args.head, args.include_worktree
        )
        report.extend(git_report)
    else:
        report.error(
            "DSL-GIT-001",
            "changes requires --base or at least one --changed-file",
            root,
        )
    if not report.has_code("DSL-GIT-001"):
        report.extend(check_changed_paths(root, changed, manifests))
    print(report.render(args.format))
    return 1 if report.failed else 0


def command_gate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    report, manifests = load_targets(args.targets or ["."], root)
    revision = args.revision or git_revision(root)
    if revision is None or REVISION.fullmatch(revision) is None:
        report.error(
            "DSL-FINDINGS-003",
            "gate requires a valid --revision or a Git checkout with a resolvable HEAD",
            root,
        )
    else:
        report_paths = [
            Path(raw) if Path(raw).is_absolute() else root / raw
            for raw in args.findings
        ]
        report.extend(gate_findings(root, manifests, report_paths, revision))
    print(report.render(args.format))
    return 1 if report.failed else 0


def command_standards(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    report, manifests = load_targets(args.targets or ["."], root)
    locked = [item for item in manifests if "standardsLock" in item.document]
    if not locked:
        report.error(
            "DSL-LOCK-001",
            "aggregate standards conformance requires at least one standardsLock",
            root,
        )
    print(report.render(args.format))
    return 1 if report.failed else 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser(
        "validate", help="validate manifests and their bound artifacts"
    )
    validate.add_argument(
        "targets",
        nargs="*",
        help="manifest files or directories; default: repository root",
    )
    validate.add_argument("--root", default=".", help="repository root")
    validate.add_argument("--format", choices=["text", "json"], default="text")
    validate.set_defaults(handler=command_validate)

    changes = subparsers.add_parser(
        "changes", help="validate manifests and ownership of changed DSL files"
    )
    changes.add_argument("--root", default=".", help="repository root")
    changes.add_argument("--base", help="accepted Git base revision")
    changes.add_argument("--head", default="HEAD", help="Git head revision")
    changes.add_argument(
        "--include-worktree",
        action="store_true",
        help="also inspect staged, unstaged, and untracked files",
    )
    changes.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="explicit repository-relative changed path; repeatable and usable in Git-free containers",
    )
    changes.add_argument("--format", choices=["text", "json"], default="text")
    changes.set_defaults(handler=command_changes)

    gate = subparsers.add_parser(
        "gate",
        help="validate manifests, help pages, and revision-bound normalized findings",
    )
    gate.add_argument(
        "targets",
        nargs="*",
        help="manifest files or directories; default: repository root",
    )
    gate.add_argument("--root", default=".", help="repository root")
    gate.add_argument(
        "--findings",
        action="append",
        default=[],
        help="wellmanifest.dsl/findings/v1 report; repeat once per producer and manifest",
    )
    gate.add_argument(
        "--revision",
        help="exact 40-character revision when Git metadata is unavailable; defaults to HEAD",
    )
    gate.add_argument("--format", choices=["text", "json"], default="text")
    gate.set_defaults(handler=command_gate)

    standards = subparsers.add_parser(
        "standards",
        help="validate manifests, artifacts, publication tiers, and immutable standards locks",
    )
    standards.add_argument(
        "targets",
        nargs="*",
        help="manifest files or directories; default: repository root",
    )
    standards.add_argument("--root", default=".", help="repository root")
    standards.add_argument("--format", choices=["text", "json"], default="text")
    standards.set_defaults(handler=command_standards)

    check = subparsers.add_parser(
        "self-test", help="run dependency-free validator regression cases"
    )
    check.set_defaults(handler=lambda _args: self_test())
    return result


def main() -> int:
    args = parser().parse_args()
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
