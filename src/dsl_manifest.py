"""Top-level manifest validation, target discovery, and changed-path ownership."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from dsl_policy import (
    validate_documentation,
    validate_finding_policy,
    validate_publication_policy,
    validate_standards_lock,
)
from dsl_primitives import (
    DOMAIN,
    MANIFEST_NAME,
    MANIFEST_SCHEMA,
    SEMVER,
    STABLE_ID,
    Report,
    check_object,
    check_string_list,
    is_string,
    matches,
    read_regular_bytes,
    read_regular_utf8,
    resolve_nonsymlink_under_root,
    safe_relative,
    str_choice,
    strict_json_loads,
    uri_is_valid,
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


@dataclass
class ValidatedManifest:
    path: Path
    document: dict[str, Any]
    owned_paths: list[str]
    artifacts: set[str]
    documentation: dict[str, Any]
    finding_policy: dict[str, Any]


def validate_manifest(
    manifest_path: Path, root: Path
) -> tuple[Report, ValidatedManifest | None]:
    report = Report()
    resolved_manifest = resolve_nonsymlink_under_root(manifest_path, root)
    if resolved_manifest is None:
        report.error(
            "DSL-PATH-001",
            "manifest is outside the repository root or traverses a symlink",
            manifest_path,
        )
        return report, None
    try:
        document = strict_json_loads(read_regular_utf8(resolved_manifest))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        report.error(
            "DSL-MANIFEST-001", f"cannot load manifest: {error}", manifest_path
        )
        return report, None

    required = {
        "schema",
        "id",
        "name",
        "version",
        "status",
        "purpose",
        "domain",
        "owners",
        "source",
        "ownedPaths",
        "artifacts",
        "namespaces",
        "projections",
        "lifecycle",
        "semantics",
        "llm",
        "documentation",
        "findingPolicy",
        "publicationPolicy",
        "conformance",
        "mappings",
    }
    manifest = check_object(
        document,
        required,
        required | {"$schema", "standardsLock"},
        "manifest",
        report,
        manifest_path,
    )
    if manifest is None:
        return report, None
    if "$schema" in manifest and not uri_is_valid(manifest.get("$schema")):
        report.error("DSL-MANIFEST-001", "$schema must be a URI", manifest_path)
    if manifest.get("schema") != MANIFEST_SCHEMA:
        report.error(
            "DSL-MANIFEST-001", f"schema must equal {MANIFEST_SCHEMA}", manifest_path
        )
    identifier = manifest.get("id")
    if not isinstance(identifier, str) or STABLE_ID.fullmatch(identifier) is None:
        report.error(
            "DSL-MANIFEST-001",
            "id is not a stable namespaced identifier",
            manifest_path,
        )
    if not is_string(manifest.get("name")) or not is_string(manifest.get("purpose")):
        report.error(
            "DSL-MANIFEST-001", "name and purpose must be non-empty", manifest_path
        )
    version = manifest.get("version")
    if not isinstance(version, str) or SEMVER.fullmatch(version) is None:
        report.error(
            "DSL-COMPAT-001", "version must use Semantic Versioning", manifest_path
        )
    status = manifest.get("status")
    if not str_choice(status, {"experimental", "stable", "deprecated"}):
        report.error("DSL-MANIFEST-001", "status is invalid", manifest_path)
    domain = manifest.get("domain")
    if not isinstance(domain, str) or DOMAIN.fullmatch(domain) is None:
        report.error("DSL-MANIFEST-001", "domain is invalid", manifest_path)

    validate_owners(manifest.get("owners"), report, manifest_path)
    source = validate_source(manifest.get("source"), root, report, manifest_path)
    owned_paths = check_string_list(
        manifest.get("ownedPaths"), "ownedPaths", report, manifest_path, nonempty=True
    )
    for index, raw in enumerate(owned_paths):
        safe_relative(raw, f"ownedPaths[{index}]", report, manifest_path)
    manifest_relative = resolved_manifest.relative_to(root.resolve()).as_posix()
    if not matches(manifest_relative, owned_paths):
        report.error(
            "DSL-OWNER-001",
            "ownedPaths must include the manifest itself",
            manifest_path,
        )
    artifacts = validate_artifacts(
        manifest.get("artifacts"),
        root,
        owned_paths,
        source.get("path") if source else None,
        report,
        manifest_path,
    )
    validate_namespaces(manifest.get("namespaces"), report, manifest_path)
    validate_projections(manifest.get("projections"), report, manifest_path)
    validate_lifecycle(manifest.get("lifecycle"), status, report, manifest_path)
    validate_semantics(manifest.get("semantics"), report, manifest_path)
    validate_llm(manifest.get("llm"), report, manifest_path)
    documentation = validate_documentation(
        manifest.get("documentation"),
        root,
        owned_paths,
        artifacts,
        report,
        manifest_path,
    )
    finding_policy = validate_finding_policy(
        manifest.get("findingPolicy"), report, manifest_path
    )
    validate_publication_policy(
        manifest.get("publicationPolicy"), manifest, report, manifest_path
    )
    if "standardsLock" in manifest:
        validate_standards_lock(manifest.get("standardsLock"), report, manifest_path)
    validate_conformance(manifest.get("conformance"), root, report, manifest_path)
    validate_mappings(manifest.get("mappings"), report, manifest_path)
    return report, ValidatedManifest(
        manifest_path,
        manifest,
        owned_paths,
        set(artifacts),
        documentation or {},
        finding_policy or {},
    )


def discover_manifests(root: Path) -> list[Path]:
    """Discover one selected tree without absorbing other checkout identities.

    A nested checkout or saved snapshot can still be validated by selecting it
    explicitly. Ordinary monorepo packages remain part of recursive discovery.
    """
    ignored = {
        ".git",
        ".venv",
        "node_modules",
        "vendor",
        "dist",
        "build",
        "__pycache__",
    }
    operational = {"leases", "sessions", "recovery", "receipts", "cache", "snapshots"}
    found: list[Path] = []
    for current, directories, files in os.walk(root):
        current_path = Path(current)
        directories[:] = sorted(
            item
            for item in directories
            if item not in ignored
            and not (current_path == root and item in {"worktrees", ".worktrees"})
            and not (current_path == root / ".subactor" and item in operational)
            and not (current_path / item / ".git").exists()
        )
        if MANIFEST_NAME in files:
            found.append(Path(current) / MANIFEST_NAME)
    return sorted(found)


def load_targets(
    targets: list[str], root: Path
) -> tuple[Report, list[ValidatedManifest]]:
    report = Report()
    discovered: list[Path] = []
    for raw in targets:
        target = Path(raw)
        if not target.is_absolute():
            target = root / target
        checked = resolve_nonsymlink_under_root(target, root)
        if checked is None:
            report.error(
                "DSL-PATH-001",
                "manifest is outside the repository root or traverses a symlink",
                target,
            )
            continue
        if checked.is_dir():
            discovered.extend(discover_manifests(checked))
        elif checked.is_file():
            discovered.append(checked)
        else:
            report.error("DSL-MANIFEST-001", "manifest target does not exist", raw)
    verified_paths: set[Path] = set()
    for item in discovered:
        checked_item = resolve_nonsymlink_under_root(item, root)
        if checked_item is None:
            report.error(
                "DSL-PATH-001",
                "manifest is outside the repository root or traverses a symlink",
                item,
            )
        else:
            verified_paths.add(checked_item)
    paths = sorted(verified_paths)
    if not paths:
        if not report.failed:
            report.error("DSL-MANIFEST-001", f"no {MANIFEST_NAME} files found", root)
        return report, []
    manifests: list[ValidatedManifest] = []
    ids: dict[str, Path] = {}
    for path in paths:
        item_report, validated = validate_manifest(path, root)
        report.extend(item_report)
        if validated is None:
            continue
        identifier = validated.document.get("id")
        if isinstance(identifier, str) and identifier in ids:
            report.error("DSL-OWNER-002", f"duplicate DSL id {identifier}", path)
        elif isinstance(identifier, str):
            ids[identifier] = path
        manifests.append(validated)
    return report, manifests


def _run_git_command(command: list[str], root: Path) -> bytes:
    return subprocess.check_output(command, cwd=root, timeout=30)


def _valid_git_revision_arg(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and not value.startswith("-")
        and not any(ord(ch) < 32 for ch in value)
        and ".." not in value
    )


def git_paths(
    root: Path, base: str, head: str, include_worktree: bool
) -> tuple[Report, set[str]]:
    report = Report()
    if not _valid_git_revision_arg(base) or not _valid_git_revision_arg(head):
        report.error("DSL-GIT-001", "invalid Git revision boundary", root)
        return report, set()
    changed: set[str] = set()
    commands = [["git", "diff", "--name-only", "-z", f"{base}...{head}"]]
    if include_worktree:
        commands.extend(
            [
                ["git", "diff", "--name-only", "-z"],
                ["git", "diff", "--cached", "--name-only", "-z"],
                ["git", "ls-files", "--others", "--exclude-standard", "-z"],
            ]
        )
    for command in commands:
        try:
            output = _run_git_command(command, root)
        except (
            FileNotFoundError,
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
        ) as error:
            report.error(
                "DSL-GIT-001", f"cannot determine changed files: {error}", root
            )
            return report, set()
        changed.update(item.decode("utf-8") for item in output.split(b"\0") if item)
    return report, changed


def is_dsl_sensitive(root: Path, path: str, manifests: list[ValidatedManifest]) -> bool:
    if any(matches(path, item.owned_paths) for item in manifests):
        return True
    pure = PurePosixPath(path)
    lower_parts = {part.lower() for part in pure.parts}
    lower_name = pure.name.lower()
    if lower_name in {
        MANIFEST_NAME,
        "contributing.md",
        "policy.md",
    } or lower_name.endswith("schema.json"):
        return True
    if pure.suffix.lower() in {".dsl", ".ebnf", ".g4", ".proto"}:
        return True
    if lower_parts & {"dsl", "schemas", "grammar", "grammars", "profiles", "spec"}:
        return True
    safe_target = resolve_nonsymlink_under_root(root / path, root)
    if safe_target is None:
        return False
    try:
        content = read_regular_bytes(
            safe_target, max_bytes=2 * 1024 * 1024, follow_symlinks=False
        )
        return b"```dsl" in content
    except (OSError, RuntimeError, ValueError):
        pass
    return False


def check_changed_paths(
    root: Path, changed: Iterable[str], manifests: list[ValidatedManifest]
) -> Report:
    report = Report()
    for path in sorted(set(changed)):
        if not is_dsl_sensitive(root, path, manifests):
            continue
        owners = [item for item in manifests if matches(path, item.owned_paths)]
        if not owners:
            report.error(
                "DSL-OWNER-001",
                "changed DSL-sensitive file has no manifest owner",
                path,
            )
            continue
        if len(owners) > 1:
            report.error(
                "DSL-OWNER-002",
                "changed DSL-sensitive file has multiple manifest owners: "
                + ", ".join(str(item.path) for item in owners),
                path,
            )
            continue
        owner = owners[0]
        manifest_relative = owner.path.resolve().relative_to(root.resolve()).as_posix()
        if path != manifest_relative and path not in owner.artifacts:
            report.error(
                "DSL-ARTIFACT-002",
                "changed DSL file is not digest-bound in its owner manifest",
                path,
            )
    return report
