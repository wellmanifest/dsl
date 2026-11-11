"""Documentation, publication, standards-lock, conformance, and mapping validators."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from dsl_primitives import (
    COMMAND_NAME,
    DIGEST,
    FINDING_CODE,
    FINDINGS_SCHEMA,
    HELP_PAGE_SECTIONS,
    MANIFEST_NAME,
    PRODUCER_ID,
    REVISION,
    SEMVER,
    STABLE_ID,
    Report,
    check_object,
    check_string_list,
    matches,
    read_regular_utf8,
    resolve_repository_path,
    str_choice,
    string_set,
    uri_is_valid,
)


def page_has_section_content(text: str, heading: str) -> bool:
    lines = text.splitlines()
    marker = f"## {heading}"
    try:
        start = lines.index(marker) + 1
    except ValueError:
        return False
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if (
            stripped
            and not stripped.startswith("#")
            and not stripped.startswith("<!--")
        ):
            return True
    return False


def validate_help_page(
    root: Path, relative: str, name: str, kind: str, report: Report
) -> None:
    resolved = resolve_repository_path(
        root, relative, f"help page {relative}", report, root / MANIFEST_NAME
    )
    if resolved is None:
        return
    expected = root / relative
    if not resolved.is_file():
        alternatives: list[str] = []
        try:
            alternatives = [
                item.name
                for item in expected.parent.iterdir()
                if item.name.casefold() == expected.name.casefold()
            ]
        except OSError:
            pass
        if alternatives:
            report.error(
                "DSL-DOC-002",
                f"help page has incorrect case; rename {expected.parent.as_posix()}/{alternatives[0]} to {relative}",
                relative,
            )
        else:
            report.error(
                "DSL-DOC-001", f"required help page is missing: {relative}", relative
            )
        return
    try:
        text = read_regular_utf8(resolved)
    except (OSError, UnicodeDecodeError, ValueError) as error:
        report.error(
            "DSL-DOC-003", f"help page cannot be read as UTF-8: {error}", relative
        )
        return
    problems: list[str] = []
    if not text.startswith(f"# {name}\n"):
        problems.append(f"exact title '# {name}'")
    for heading in HELP_PAGE_SECTIONS[kind]:
        if not page_has_section_content(text, heading):
            problems.append(f"non-empty '## {heading}' section")
    if problems:
        report.error(
            "DSL-DOC-003",
            f"incomplete help page {relative}; required: {', '.join(problems)}",
            relative,
        )


def validate_documentation(
    value: Any,
    root: Path,
    owned_paths: list[str],
    artifacts: dict[str, dict[str, Any]],
    report: Report,
    manifest_path: Path,
) -> dict[str, Any] | None:
    keys = {
        "vocabularyKind",
        "commandRoot",
        "errorRoot",
        "criticalRoot",
        "commands",
        "errorCodes",
        "criticalCodes",
    }
    item = check_object(value, keys, keys, "documentation", report, manifest_path)
    if item is None:
        return None
    vocabulary_kind = item.get("vocabularyKind")
    if not str_choice(vocabulary_kind, {"commands", "documents"}):
        report.error(
            "DSL-DOC-001",
            "documentation.vocabularyKind must be commands or documents",
            manifest_path,
        )
    roots = {
        "commandRoot": "docs",
        "errorRoot": "docs/ERROR",
        "criticalRoot": "docs/CRITICAL",
    }
    for field, expected in roots.items():
        if item.get(field) != expected:
            report.error(
                "DSL-DOC-001", f"documentation.{field} must equal {expected}", expected
            )
    catalogs: dict[str, tuple[list[str], re.Pattern[str], str, str]] = {
        "commands": (
            check_string_list(
                item.get("commands"),
                "documentation.commands",
                report,
                manifest_path,
                nonempty=vocabulary_kind == "commands",
            ),
            COMMAND_NAME,
            "command",
            "docs",
        ),
        "errorCodes": (
            check_string_list(
                item.get("errorCodes"),
                "documentation.errorCodes",
                report,
                manifest_path,
            ),
            FINDING_CODE,
            "error",
            "docs/ERROR",
        ),
        "criticalCodes": (
            check_string_list(
                item.get("criticalCodes"),
                "documentation.criticalCodes",
                report,
                manifest_path,
            ),
            FINDING_CODE,
            "critical",
            "docs/CRITICAL",
        ),
    }
    overlap = set(catalogs["errorCodes"][0]) & set(catalogs["criticalCodes"][0])
    if overlap:
        report.error(
            "DSL-DOC-001",
            "errorCodes and criticalCodes must be disjoint: "
            + ", ".join(sorted(overlap)),
            manifest_path,
        )
    for field, (names, pattern, kind, page_root) in catalogs.items():
        for name in names:
            relative = f"{page_root}/{name}.md"
            if pattern.fullmatch(name) is None:
                report.error(
                    "DSL-DOC-001",
                    f"documentation.{field} contains an invalid uppercase name: {name}; help path: {relative}",
                    relative,
                )
                continue
            if not matches(relative, owned_paths):
                report.error(
                    "DSL-DOC-004",
                    f"help page is outside ownedPaths: {relative}",
                    relative,
                )
            artifact = artifacts.get(relative)
            if artifact is None:
                report.error(
                    "DSL-DOC-004",
                    f"help page is not digest-bound as an artifact: {relative}",
                    relative,
                )
            elif artifact.get("role") != "documentation":
                report.error(
                    "DSL-DOC-004",
                    f"help page artifact must use role=documentation: {relative}",
                    relative,
                )
            validate_help_page(root, relative, name, kind, report)
    return item


def required_publication_tier(manifest: dict[str, Any]) -> str:
    semantics = manifest.get("semantics")
    llm = manifest.get("llm")
    conformance = manifest.get("conformance")
    effect = semantics.get("effectModel") if isinstance(semantics, dict) else None
    mode = llm.get("mode") if isinstance(llm, dict) else None
    raw_levels = conformance.get("levels") if isinstance(conformance, dict) else None
    level_set = string_set(raw_levels)
    if effect == "controlled-effects":
        return "controlled"
    if (
        str_choice(effect, {"declarative-policy", "propose-only"})
        or str_choice(mode, {"input", "output", "bidirectional"})
        or bool(level_set & {"runtime", "llm-boundary"})
    ):
        return "review"
    return "basic"


def validate_publication_policy(
    value: Any, manifest: dict[str, Any], report: Report, path: Path
) -> None:
    keys = {
        "declaredTier",
        "deterministic",
        "independentReview",
        "externalAuthority",
        "runtimeIsolation",
    }
    item = check_object(value, keys, keys, "publicationPolicy", report, path)
    if item is None:
        return
    tier = item.get("declaredTier")
    required = required_publication_tier(manifest)
    if not str_choice(tier, {"basic", "review", "controlled"}):
        report.error("DSL-PUBLICATION-001", "publication tier is invalid", path)
    elif tier != required:
        report.error(
            "DSL-PUBLICATION-001",
            f"publication tier must equal the derived tier {required}",
            path,
        )
    if item.get("deterministic") is not True:
        report.error(
            "DSL-PUBLICATION-001", "publication gate must be deterministic", path
        )
    if (
        required in {"review", "controlled"}
        and item.get("independentReview") is not True
    ):
        report.error(
            "DSL-PUBLICATION-001",
            f"{required} tier requires independent review",
            path,
        )
    if required == "controlled" and (
        item.get("externalAuthority") is not True
        or item.get("runtimeIsolation") is not True
    ):
        report.error(
            "DSL-PUBLICATION-001",
            "controlled tier requires external authority and runtime isolation",
            path,
        )
    for field in ("independentReview", "externalAuthority", "runtimeIsolation"):
        if not isinstance(item.get(field), bool):
            report.error(
                "DSL-PUBLICATION-001",
                f"publicationPolicy.{field} must be boolean",
                path,
            )


def validate_standards_lock(value: Any, report: Report, path: Path) -> None:
    lock = check_object(
        value,
        {"schema", "entries"},
        {"schema", "entries"},
        "standardsLock",
        report,
        path,
    )
    if lock is None:
        return
    if lock.get("schema") != "wellmanifest.standards-lock/v1":
        report.error("DSL-LOCK-001", "standardsLock.schema is not supported", path)
    entries = lock.get("entries")
    if not isinstance(entries, list) or not 1 <= len(entries) <= 32:
        report.error("DSL-LOCK-001", "standardsLock.entries is invalid", path)
        return
    standards: set[str] = set()
    for index, raw in enumerate(entries):
        fields = {"standard", "version", "repository", "revision", "contracts"}
        entry = check_object(
            raw, fields, fields, f"standardsLock.entries[{index}]", report, path
        )
        if entry is None:
            continue
        standard = entry.get("standard")
        if not isinstance(standard, str) or STABLE_ID.fullmatch(standard) is None:
            report.error(
                "DSL-LOCK-001",
                f"standardsLock.entries[{index}].standard is invalid",
                path,
            )
        elif standard in standards:
            report.error("DSL-LOCK-001", f"duplicate standard pin: {standard}", path)
        else:
            standards.add(standard)
        version = entry.get("version")
        if not isinstance(version, str) or SEMVER.fullmatch(version) is None:
            report.error(
                "DSL-LOCK-001",
                f"standardsLock.entries[{index}].version is invalid",
                path,
            )
        if not uri_is_valid(entry.get("repository")):
            report.error(
                "DSL-LOCK-001",
                f"standardsLock.entries[{index}].repository is invalid",
                path,
            )
        revision = entry.get("revision")
        if not isinstance(revision, str) or REVISION.fullmatch(revision) is None:
            report.error(
                "DSL-LOCK-001",
                f"standardsLock.entries[{index}].revision is invalid",
                path,
            )
        contracts = entry.get("contracts")
        if not isinstance(contracts, list) or not 1 <= len(contracts) <= 32:
            report.error(
                "DSL-LOCK-001",
                f"standardsLock.entries[{index}].contracts is invalid",
                path,
            )
            continue
        refs: set[str] = set()
        for contract_index, raw_contract in enumerate(contracts):
            contract = check_object(
                raw_contract,
                {"ref", "digest"},
                {"ref", "digest"},
                f"standardsLock.entries[{index}].contracts[{contract_index}]",
                report,
                path,
            )
            if contract is None:
                continue
            reference = contract.get("ref")
            if not uri_is_valid(reference):
                report.error("DSL-LOCK-001", "standard contract ref is invalid", path)
            elif reference in refs:
                report.error(
                    "DSL-LOCK-001", f"duplicate contract pin: {reference}", path
                )
            else:
                refs.add(reference)
            digest = contract.get("digest")
            if not isinstance(digest, str) or DIGEST.fullmatch(digest) is None:
                report.error(
                    "DSL-LOCK-001", "standard contract digest is invalid", path
                )


def validate_finding_policy(
    value: Any, report: Report, path: Path
) -> dict[str, Any] | None:
    keys = {
        "schema",
        "requiredProducers",
        "securityProducers",
        "blockingSeverities",
        "requireEvaluable",
        "blockUnresolvedSecurity",
    }
    item = check_object(value, keys, keys, "findingPolicy", report, path)
    if item is None:
        return None
    if item.get("schema") != FINDINGS_SCHEMA:
        report.error(
            "DSL-MANIFEST-001",
            f"findingPolicy.schema must equal {FINDINGS_SCHEMA}",
            path,
        )
    required = check_string_list(
        item.get("requiredProducers"),
        "findingPolicy.requiredProducers",
        report,
        path,
        nonempty=True,
    )
    security = check_string_list(
        item.get("securityProducers"),
        "findingPolicy.securityProducers",
        report,
        path,
        nonempty=True,
    )
    for producer in required + security:
        if PRODUCER_ID.fullmatch(producer) is None:
            report.error(
                "DSL-MANIFEST-001", f"invalid findings producer id: {producer}", path
            )
    missing = sorted(set(security) - set(required))
    if missing:
        report.error(
            "DSL-MANIFEST-001",
            "securityProducers must also be requiredProducers: " + ", ".join(missing),
            path,
        )
    severities = check_string_list(
        item.get("blockingSeverities"),
        "findingPolicy.blockingSeverities",
        report,
        path,
        nonempty=True,
        allowed={"info", "warning", "error", "critical"},
    )
    if "critical" not in severities:
        report.error(
            "DSL-MANIFEST-001", "blockingSeverities must include critical", path
        )
    if item.get("requireEvaluable") is not True:
        report.error(
            "DSL-MANIFEST-001", "findingPolicy.requireEvaluable must be true", path
        )
    if item.get("blockUnresolvedSecurity") is not True:
        report.error(
            "DSL-MANIFEST-001",
            "findingPolicy.blockUnresolvedSecurity must be true",
            path,
        )
    return item
