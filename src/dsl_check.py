#!/usr/bin/env python3
"""Deterministic conformance gate for wellmanifest DSL manifests."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable
from urllib.parse import urlparse


MANIFEST_NAME = "dsl-manifest.json"
MANIFEST_SCHEMA = "wellmanifest.dsl/manifest/v1"
SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
STABLE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*[a-z0-9]$")
DIGEST = re.compile(r"^sha256:([a-f0-9]{64})$")
REVISION = re.compile(r"^[a-f0-9]{40}$")
DOMAIN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
PREFIX = re.compile(r"^[a-z][a-z0-9._-]*$")
MEDIA_TYPE = re.compile(r"^[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+$")


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    path: str = ""
    severity: str = "error"


class Report:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def error(self, code: str, message: str, path: str | Path = "") -> None:
        self.findings.append(Finding(code, message, str(path)))

    @property
    def failed(self) -> bool:
        return any(item.severity == "error" for item in self.findings)

    def has_code(self, code: str) -> bool:
        return any(item.code == code for item in self.findings)

    def extend(self, other: "Report") -> None:
        self.findings.extend(other.findings)

    def render(self, output_format: str) -> str:
        if output_format == "json":
            return json.dumps(
                {
                    "schema": "wellmanifest.dsl/check-result/v1",
                    "status": "failed" if self.failed else "passed",
                    "findings": [asdict(item) for item in self.findings],
                },
                indent=2,
                sort_keys=True,
            )
        if not self.findings:
            return "DSL-PASS: passed (0 errors)"
        lines = []
        for item in self.findings:
            location = f" [{item.path}]" if item.path else ""
            lines.append(f"{item.code} {item.severity.upper()}: {item.message}{location}")
        errors = sum(item.severity == "error" for item in self.findings)
        lines.append(f"DSL-FAIL: failed ({errors} errors)")
        return "\n".join(lines)


def is_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def unique(values: list[Any]) -> bool:
    encoded = [json.dumps(value, sort_keys=True, separators=(",", ":")) for value in values]
    return len(encoded) == len(set(encoded))


def check_object(
    value: Any,
    required: set[str],
    allowed: set[str],
    label: str,
    report: Report,
    path: Path,
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        report.error("DSL-MANIFEST-001", f"{label} must be an object", path)
        return None
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - allowed)
    if missing:
        report.error("DSL-MANIFEST-001", f"{label} misses fields: {', '.join(missing)}", path)
    if unknown:
        report.error("DSL-MANIFEST-001", f"{label} has unknown fields: {', '.join(unknown)}", path)
    return value


def check_string_list(
    value: Any,
    label: str,
    report: Report,
    path: Path,
    *,
    nonempty: bool = False,
    allowed: set[str] | None = None,
) -> list[str]:
    if not isinstance(value, list) or any(not is_string(item) for item in value):
        report.error("DSL-MANIFEST-001", f"{label} must be an array of non-empty strings", path)
        return []
    if nonempty and not value:
        report.error("DSL-MANIFEST-001", f"{label} must not be empty", path)
    if not unique(value):
        report.error("DSL-MANIFEST-001", f"{label} contains duplicates", path)
    if allowed is not None:
        invalid = sorted(set(value) - allowed)
        if invalid:
            report.error("DSL-MANIFEST-001", f"{label} has invalid values: {', '.join(invalid)}", path)
    return value


def safe_relative(raw: Any, label: str, report: Report, manifest_path: Path) -> str | None:
    if not is_string(raw):
        report.error("DSL-PATH-001", f"{label} must be a non-empty relative path", manifest_path)
        return None
    if "\\" in raw or re.match(r"^[A-Za-z]:", raw):
        report.error("DSL-PATH-001", f"{label} must use repository-relative POSIX syntax", manifest_path)
        return None
    candidate = PurePosixPath(raw)
    if candidate.is_absolute() or ".." in candidate.parts or raw in {".", ".."}:
        report.error("DSL-PATH-001", f"{label} escapes the repository: {raw}", manifest_path)
        return None
    return raw


def resolve_repository_path(root: Path, raw: str, label: str, report: Report, manifest_path: Path) -> Path | None:
    safe = safe_relative(raw, label, report, manifest_path)
    if safe is None:
        return None
    root_resolved = root.resolve()
    try:
        target = (root_resolved / safe).resolve(strict=False)
    except (OSError, RuntimeError) as error:
        report.error("DSL-PATH-001", f"{label} cannot be resolved safely: {error}", manifest_path)
        return None
    try:
        target.relative_to(root_resolved)
    except ValueError:
        report.error("DSL-PATH-001", f"{label} resolves outside the repository: {raw}", manifest_path)
        return None
    return target


def matches(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def uri_is_valid(value: Any) -> bool:
    if not is_string(value):
        return False
    parsed = urlparse(value)
    return bool(parsed.scheme)


def validate_owners(value: Any, report: Report, path: Path) -> None:
    if not isinstance(value, list) or not value:
        report.error("DSL-MANIFEST-001", "owners must be a non-empty array", path)
        return
    if not unique(value):
        report.error("DSL-MANIFEST-001", "owners contains duplicates", path)
    for index, owner in enumerate(value):
        item = check_object(
            owner,
            {"kind", "id", "responsibilities"},
            {"kind", "id", "responsibilities"},
            f"owners[{index}]",
            report,
            path,
        )
        if item is None:
            continue
        if item.get("kind") not in {"repository", "organization", "team", "person"}:
            report.error("DSL-MANIFEST-001", f"owners[{index}].kind is invalid", path)
        if not is_string(item.get("id")):
            report.error("DSL-MANIFEST-001", f"owners[{index}].id must be non-empty", path)
        check_string_list(
            item.get("responsibilities"),
            f"owners[{index}].responsibilities",
            report,
            path,
            nonempty=True,
            allowed={"semantics", "validation", "compatibility", "runtime", "security"},
        )


def validate_source(value: Any, root: Path, report: Report, path: Path) -> dict[str, Any] | None:
    required = {"repository", "path", "canonical", "mediaType", "selectors"}
    allowed = required | {"revision", "declaredVersion"}
    source = check_object(value, required, allowed, "source", report, path)
    if source is None:
        return None
    if not is_string(source.get("repository")):
        report.error("DSL-MANIFEST-001", "source.repository must be non-empty", path)
    source_path = source.get("path")
    if safe_relative(source_path, "source.path", report, path):
        resolved = resolve_repository_path(root, source_path, "source.path", report, path)
        if resolved is not None and not resolved.is_file():
            report.error("DSL-PATH-002", f"source.path does not exist: {source_path}", path)
    revision = source.get("revision")
    if revision is not None and (not isinstance(revision, str) or REVISION.fullmatch(revision) is None):
        report.error("DSL-MANIFEST-001", "source.revision must be a 40-character lowercase Git SHA", path)
    if "declaredVersion" in source and not is_string(source.get("declaredVersion")):
        report.error("DSL-MANIFEST-001", "source.declaredVersion must be non-empty", path)
    if source.get("canonical") not in {"json-ast", "protobuf", "text", "markdown-embedded", "other"}:
        report.error("DSL-MANIFEST-001", "source.canonical is invalid", path)
    media_type = source.get("mediaType")
    if not isinstance(media_type, str) or MEDIA_TYPE.fullmatch(media_type) is None:
        report.error("DSL-MANIFEST-001", "source.mediaType is invalid", path)
    selectors = check_string_list(source.get("selectors"), "source.selectors", report, path)
    if source.get("canonical") == "markdown-embedded" and not selectors:
        report.error("DSL-MANIFEST-001", "markdown-embedded sources require selectors", path)
    return source


def validate_artifacts(
    value: Any,
    root: Path,
    owned_paths: list[str],
    source_path: str | None,
    report: Report,
    manifest_path: Path,
) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list) or not value:
        report.error("DSL-MANIFEST-001", "artifacts must be a non-empty array", manifest_path)
        return {}
    result: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(value):
        artifact = check_object(
            raw,
            {"path", "role", "digest"},
            {"path", "role", "digest"},
            f"artifacts[{index}]",
            report,
            manifest_path,
        )
        if artifact is None:
            continue
        artifact_path = safe_relative(artifact.get("path"), f"artifacts[{index}].path", report, manifest_path)
        if artifact_path is None:
            continue
        if artifact_path in result:
            report.error("DSL-MANIFEST-001", f"duplicate artifact path: {artifact_path}", manifest_path)
            continue
        result[artifact_path] = artifact
        if not matches(artifact_path, owned_paths):
            report.error("DSL-ARTIFACT-001", f"artifact is outside ownedPaths: {artifact_path}", manifest_path)
        if artifact.get("role") not in {
            "normative-source", "schema", "grammar", "parser-contract",
            "serializer-contract", "profile", "example",
        }:
            report.error("DSL-MANIFEST-001", f"artifact role is invalid: {artifact.get('role')}", manifest_path)
        digest = artifact.get("digest")
        if not isinstance(digest, str) or DIGEST.fullmatch(digest) is None:
            report.error("DSL-HASH-002", f"artifact digest is invalid: {artifact_path}", manifest_path)
        resolved = resolve_repository_path(root, artifact_path, f"artifact {artifact_path}", report, manifest_path)
        if resolved is None:
            continue
        if not resolved.is_file():
            report.error("DSL-PATH-002", f"artifact does not exist: {artifact_path}", manifest_path)
        elif isinstance(digest, str) and DIGEST.fullmatch(digest):
            try:
                observed_digest = sha256(resolved)
            except OSError as error:
                report.error("DSL-PATH-002", f"artifact cannot be read: {artifact_path}: {error}", manifest_path)
            else:
                if observed_digest != digest:
                    report.error("DSL-HASH-001", f"artifact digest is stale: {artifact_path}", manifest_path)
    if source_path:
        source_artifact = result.get(source_path)
        if source_artifact is None or source_artifact.get("role") != "normative-source":
            report.error("DSL-ARTIFACT-001", "source.path must be a normative-source artifact", manifest_path)
    return result


def validate_namespaces(value: Any, report: Report, path: Path) -> None:
    if not isinstance(value, list) or not unique(value):
        report.error("DSL-MANIFEST-001", "namespaces must be a unique array", path)
        return
    prefixes: set[str] = set()
    for index, raw in enumerate(value):
        item = check_object(raw, {"prefix", "uri"}, {"prefix", "uri"}, f"namespaces[{index}]", report, path)
        if item is None:
            continue
        prefix = item.get("prefix")
        if not isinstance(prefix, str) or PREFIX.fullmatch(prefix) is None:
            report.error("DSL-MANIFEST-001", f"namespaces[{index}].prefix is invalid", path)
        elif prefix in prefixes:
            report.error("DSL-MANIFEST-001", f"duplicate namespace prefix: {prefix}", path)
        prefixes.add(str(prefix))
        if not uri_is_valid(item.get("uri")):
            report.error("DSL-MANIFEST-001", f"namespaces[{index}].uri is invalid", path)


def validate_projections(value: Any, report: Report, path: Path) -> None:
    if not isinstance(value, list) or not unique(value):
        report.error("DSL-MANIFEST-001", "projections must be a unique array", path)
        return
    for index, raw in enumerate(value):
        item = check_object(
            raw,
            {"name", "mediaType", "direction", "lossless"},
            {"name", "mediaType", "direction", "lossless"},
            f"projections[{index}]",
            report,
            path,
        )
        if item is None:
            continue
        if not is_string(item.get("name")) or not is_string(item.get("mediaType")):
            report.error("DSL-MANIFEST-001", f"projections[{index}] names and media types must be non-empty", path)
        if item.get("direction") not in {"bidirectional", "from-canonical", "to-canonical"}:
            report.error("DSL-MANIFEST-001", f"projections[{index}].direction is invalid", path)
        if not isinstance(item.get("lossless"), bool):
            report.error("DSL-MANIFEST-001", f"projections[{index}].lossless must be boolean", path)


def validate_lifecycle(value: Any, status: Any, report: Report, path: Path) -> None:
    keys = {"compatibility", "stability", "breaking", "additive", "fix"}
    item = check_object(value, keys, keys, "lifecycle", report, path)
    if item is None:
        return
    expected = {
        "compatibility": "semver", "breaking": "major", "additive": "minor", "fix": "patch",
    }
    for key, expected_value in expected.items():
        if item.get(key) != expected_value:
            report.error("DSL-COMPAT-001", f"lifecycle.{key} must equal {expected_value}", path)
    if item.get("stability") not in {"experimental", "stable", "deprecated"}:
        report.error("DSL-MANIFEST-001", "lifecycle.stability is invalid", path)
    if item.get("stability") != status:
        report.error("DSL-COMPAT-001", "status and lifecycle.stability must match", path)


def validate_semantics(value: Any, report: Report, path: Path) -> None:
    keys = {"effectModel", "unknownPolicy", "authoritySchema"}
    item = check_object(value, keys, keys, "semantics", report, path)
    if item is None:
        return
    effect = item.get("effectModel")
    if effect not in {"descriptive", "declarative-policy", "propose-only", "controlled-effects"}:
        report.error("DSL-MANIFEST-001", "semantics.effectModel is invalid", path)
    if item.get("unknownPolicy") not in {"preserve", "reject", "domain-defined"}:
        report.error("DSL-MANIFEST-001", "semantics.unknownPolicy is invalid", path)
    authority = item.get("authoritySchema")
    if effect == "controlled-effects" and not is_string(authority):
        report.error("DSL-AUTH-001", "controlled-effects requires authoritySchema", path)
    if effect != "controlled-effects" and authority is not None:
        report.error("DSL-AUTH-001", "authoritySchema is allowed only for controlled-effects", path)


def validate_llm(value: Any, report: Report, path: Path) -> None:
    keys = {
        "mode", "requestSchemas", "responseSchemas", "naturalLanguage",
        "sourceSchema", "modelAuthority", "strict",
    }
    item = check_object(value, keys, keys, "llm", report, path)
    if item is None:
        return
    mode = item.get("mode")
    if mode not in {"none", "input", "output", "bidirectional"}:
        report.error("DSL-LLM-001", "llm.mode is invalid", path)
        mode = "invalid"
    requests = check_string_list(item.get("requestSchemas"), "llm.requestSchemas", report, path)
    responses = check_string_list(item.get("responseSchemas"), "llm.responseSchemas", report, path)
    if mode in {"input", "bidirectional"} and not requests:
        report.error("DSL-LLM-001", f"llm.mode={mode} requires requestSchemas", path)
    if mode in {"output", "bidirectional"} and not responses:
        report.error("DSL-LLM-001", f"llm.mode={mode} requires responseSchemas", path)
    if mode == "none" and (requests or responses):
        report.error("DSL-LLM-001", "llm.mode=none forbids requestSchemas and responseSchemas", path)
    natural = item.get("naturalLanguage")
    if natural not in {"forbidden", "typed-source-only"}:
        report.error("DSL-LLM-001", "llm.naturalLanguage is invalid", path)
    source_schema = item.get("sourceSchema")
    if natural == "typed-source-only" and not is_string(source_schema):
        report.error("DSL-LLM-001", "typed-source-only requires sourceSchema", path)
    if natural == "forbidden" and source_schema is not None:
        report.error("DSL-LLM-001", "forbidden natural language requires sourceSchema=null", path)
    authority = item.get("modelAuthority")
    if mode == "none" and authority != "none":
        report.error("DSL-LLM-001", "llm.mode=none requires modelAuthority=none", path)
    if mode != "none" and authority != "propose-only":
        report.error("DSL-LLM-001", "LLM-enabled DSLs require modelAuthority=propose-only", path)
    if item.get("strict") is not True:
        report.error("DSL-LLM-001", "llm.strict must be true", path)


def validate_conformance(value: Any, root: Path, report: Report, path: Path) -> None:
    keys = {"levels", "commands", "validExamples", "invalidExamples"}
    item = check_object(value, keys, keys, "conformance", report, path)
    if item is None:
        return
    check_string_list(
        item.get("levels"), "conformance.levels", report, path, nonempty=True,
        allowed={"manifest", "contract", "runtime", "llm-boundary"},
    )
    check_string_list(item.get("commands"), "conformance.commands", report, path, nonempty=True)
    for field in ("validExamples", "invalidExamples"):
        examples = check_string_list(item.get(field), f"conformance.{field}", report, path)
        for raw in examples:
            resolved = resolve_repository_path(root, raw, f"conformance.{field}", report, path)
            if resolved is not None and not resolved.is_file():
                report.error("DSL-CONFORMANCE-001", f"example does not exist: {raw}", path)


def validate_mappings(value: Any, report: Report, path: Path) -> None:
    if not isinstance(value, list) or not unique(value):
        report.error("DSL-MANIFEST-001", "mappings must be a unique array", path)
        return
    for index, raw in enumerate(value):
        required = {"standard", "version", "relation"}
        item = check_object(raw, required, required | {"uri"}, f"mappings[{index}]", report, path)
        if item is None:
            continue
        if not is_string(item.get("standard")) or not is_string(item.get("version")):
            report.error("DSL-MANIFEST-001", f"mappings[{index}] names and versions must be non-empty", path)
        if item.get("relation") not in {"extends", "implements", "maps-to", "compatible-with"}:
            report.error("DSL-MANIFEST-001", f"mappings[{index}].relation is invalid", path)
        if "uri" in item and not uri_is_valid(item.get("uri")):
            report.error("DSL-MANIFEST-001", f"mappings[{index}].uri is invalid", path)


@dataclass
class ValidatedManifest:
    path: Path
    document: dict[str, Any]
    owned_paths: list[str]
    artifacts: set[str]


def validate_manifest(manifest_path: Path, root: Path) -> tuple[Report, ValidatedManifest | None]:
    report = Report()
    try:
        resolved_manifest = manifest_path.resolve(strict=False)
        resolved_manifest.relative_to(root.resolve())
    except (OSError, RuntimeError, ValueError):
        report.error("DSL-PATH-001", "manifest is outside the repository root", manifest_path)
        return report, None
    try:
        document = json.loads(resolved_manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        report.error("DSL-MANIFEST-001", f"cannot load manifest: {error}", manifest_path)
        return report, None

    required = {
        "schema", "id", "name", "version", "status", "purpose", "domain", "owners",
        "source", "ownedPaths", "artifacts", "namespaces", "projections", "lifecycle",
        "semantics", "llm", "conformance", "mappings",
    }
    manifest = check_object(document, required, required | {"$schema"}, "manifest", report, manifest_path)
    if manifest is None:
        return report, None
    if "$schema" in manifest and not uri_is_valid(manifest.get("$schema")):
        report.error("DSL-MANIFEST-001", "$schema must be a URI", manifest_path)
    if manifest.get("schema") != MANIFEST_SCHEMA:
        report.error("DSL-MANIFEST-001", f"schema must equal {MANIFEST_SCHEMA}", manifest_path)
    identifier = manifest.get("id")
    if not isinstance(identifier, str) or STABLE_ID.fullmatch(identifier) is None:
        report.error("DSL-MANIFEST-001", "id is not a stable namespaced identifier", manifest_path)
    if not is_string(manifest.get("name")) or not is_string(manifest.get("purpose")):
        report.error("DSL-MANIFEST-001", "name and purpose must be non-empty", manifest_path)
    version = manifest.get("version")
    if not isinstance(version, str) or SEMVER.fullmatch(version) is None:
        report.error("DSL-COMPAT-001", "version must use Semantic Versioning", manifest_path)
    status = manifest.get("status")
    if status not in {"experimental", "stable", "deprecated"}:
        report.error("DSL-MANIFEST-001", "status is invalid", manifest_path)
    domain = manifest.get("domain")
    if not isinstance(domain, str) or DOMAIN.fullmatch(domain) is None:
        report.error("DSL-MANIFEST-001", "domain is invalid", manifest_path)

    validate_owners(manifest.get("owners"), report, manifest_path)
    source = validate_source(manifest.get("source"), root, report, manifest_path)
    owned_paths = check_string_list(manifest.get("ownedPaths"), "ownedPaths", report, manifest_path, nonempty=True)
    for index, raw in enumerate(owned_paths):
        safe_relative(raw, f"ownedPaths[{index}]", report, manifest_path)
    try:
        manifest_relative = manifest_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        report.error("DSL-PATH-001", "manifest is outside the repository root", manifest_path)
    else:
        if not matches(manifest_relative, owned_paths):
            report.error("DSL-OWNER-001", "ownedPaths must include the manifest itself", manifest_path)
    artifacts = validate_artifacts(
        manifest.get("artifacts"), root, owned_paths,
        source.get("path") if source else None, report, manifest_path,
    )
    validate_namespaces(manifest.get("namespaces"), report, manifest_path)
    validate_projections(manifest.get("projections"), report, manifest_path)
    validate_lifecycle(manifest.get("lifecycle"), status, report, manifest_path)
    validate_semantics(manifest.get("semantics"), report, manifest_path)
    validate_llm(manifest.get("llm"), report, manifest_path)
    validate_conformance(manifest.get("conformance"), root, report, manifest_path)
    validate_mappings(manifest.get("mappings"), report, manifest_path)
    return report, ValidatedManifest(manifest_path, manifest, owned_paths, set(artifacts))


def discover_manifests(root: Path) -> list[Path]:
    ignored = {".git", ".venv", "node_modules", "vendor", "dist", "build", "__pycache__"}
    found: list[Path] = []
    for current, directories, files in os.walk(root):
        directories[:] = sorted(item for item in directories if item not in ignored)
        if MANIFEST_NAME in files:
            found.append(Path(current) / MANIFEST_NAME)
    return sorted(found)


def load_targets(targets: list[str], root: Path) -> tuple[Report, list[ValidatedManifest]]:
    report = Report()
    paths: list[Path] = []
    for raw in targets:
        target = Path(raw)
        if not target.is_absolute():
            target = root / target
        if target.is_dir():
            paths.extend(discover_manifests(target))
        elif target.is_file():
            paths.append(target)
        else:
            report.error("DSL-MANIFEST-001", "manifest target does not exist", raw)
    paths = sorted(set(item.resolve() for item in paths))
    if not paths:
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


def git_paths(root: Path, base: str, head: str, include_worktree: bool) -> tuple[Report, set[str]]:
    report = Report()
    changed: set[str] = set()
    commands = [["git", "diff", "--name-only", "-z", f"{base}...{head}"]]
    if include_worktree:
        commands.extend([
            ["git", "diff", "--name-only", "-z"],
            ["git", "diff", "--cached", "--name-only", "-z"],
            ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        ])
    for command in commands:
        try:
            output = subprocess.check_output(command, cwd=root)
        except (FileNotFoundError, subprocess.CalledProcessError) as error:
            report.error("DSL-GIT-001", f"cannot determine changed files: {error}", root)
            return report, set()
        changed.update(item.decode("utf-8") for item in output.split(b"\0") if item)
    return report, changed


def is_dsl_sensitive(root: Path, path: str, manifests: list[ValidatedManifest]) -> bool:
    if any(matches(path, item.owned_paths) for item in manifests):
        return True
    pure = PurePosixPath(path)
    lower_parts = {part.lower() for part in pure.parts}
    lower_name = pure.name.lower()
    if lower_name in {MANIFEST_NAME, "contributing.md", "policy.md"} or lower_name.endswith("schema.json"):
        return True
    if pure.suffix.lower() in {".dsl", ".ebnf", ".g4", ".proto"}:
        return True
    if lower_parts & {"dsl", "schemas", "grammar", "grammars", "profiles", "spec"}:
        return True
    file_path = root / path
    try:
        if file_path.is_file() and file_path.stat().st_size <= 2 * 1024 * 1024:
            return b"```dsl" in file_path.read_bytes()
    except OSError:
        pass
    return False


def check_changed_paths(root: Path, changed: Iterable[str], manifests: list[ValidatedManifest]) -> Report:
    report = Report()
    for path in sorted(set(changed)):
        if not is_dsl_sensitive(root, path, manifests):
            continue
        owners = [item for item in manifests if matches(path, item.owned_paths)]
        if not owners:
            report.error("DSL-OWNER-001", "changed DSL-sensitive file has no manifest owner", path)
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
            report.error("DSL-ARTIFACT-002", "changed DSL file is not digest-bound in its owner manifest", path)
    return report


def valid_example_document(source_digest: str) -> dict[str, Any]:
    return {
        "$schema": "https://example.test/dsl-manifest.schema.json",
        "schema": MANIFEST_SCHEMA,
        "id": "example.policy.rules",
        "name": "Example policy rules",
        "version": "1.0.0",
        "status": "experimental",
        "purpose": "Self-test policy DSL",
        "domain": "software-governance",
        "owners": [{
            "kind": "repository", "id": "example/repository",
            "responsibilities": ["semantics", "validation", "compatibility"],
        }],
        "source": {
            "repository": "https://example.test/repository",
            "path": "CONTRIBUTING.md",
            "declaredVersion": "1",
            "canonical": "markdown-embedded",
            "mediaType": "text/markdown",
            "selectors": ["fenced-code:dsl"],
        },
        "ownedPaths": ["CONTRIBUTING.md", MANIFEST_NAME],
        "artifacts": [{
            "path": "CONTRIBUTING.md", "role": "normative-source", "digest": source_digest,
        }],
        "namespaces": [{"prefix": "example", "uri": "https://example.test/"}],
        "projections": [],
        "lifecycle": {
            "compatibility": "semver", "stability": "experimental",
            "breaking": "major", "additive": "minor", "fix": "patch",
        },
        "semantics": {
            "effectModel": "declarative-policy", "unknownPolicy": "reject", "authoritySchema": None,
        },
        "llm": {
            "mode": "none", "requestSchemas": [], "responseSchemas": [],
            "naturalLanguage": "typed-source-only", "sourceSchema": "wellmanifest.dsl/source/v1",
            "modelAuthority": "none", "strict": True,
        },
        "conformance": {
            "levels": ["manifest"], "commands": ["python3 check.py"],
            "validExamples": [], "invalidExamples": [],
        },
        "mappings": [],
    }


def self_test() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="wellmanifest-dsl-") as temporary:
        root = Path(temporary)
        source = root / "CONTRIBUTING.md"
        source.write_text("```dsl\nDOCUMENT EXAMPLE\nVERSION 1\n```\n", encoding="utf-8")
        manifest_path = root / MANIFEST_NAME
        document = valid_example_document(sha256(source))
        manifest_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

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
        manifest_path.write_text(json.dumps(invalid_llm, indent=2) + "\n", encoding="utf-8")
        llm_report, _ = validate_manifest(manifest_path, root)
        if not llm_report.has_code("DSL-LLM-001"):
            failures.append("invalid LLM boundary was not rejected")

        document["source"]["path"] = "../outside.dsl"
        manifest_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        path_report, _ = validate_manifest(manifest_path, root)
        if not path_report.has_code("DSL-PATH-001"):
            failures.append("repository path escape was not rejected")

        document = valid_example_document(sha256(source))
        manifest_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        valid_report, valid_manifest = validate_manifest(manifest_path, root)
        grammar = root / "grammar" / "example.ebnf"
        grammar.parent.mkdir()
        grammar.write_text("document = 'EXAMPLE';\n", encoding="utf-8")
        ownership = check_changed_paths(root, ["grammar/example.ebnf"], [valid_manifest] if valid_manifest else [])
        if valid_report.failed or not ownership.has_code("DSL-OWNER-001"):
            failures.append("unclaimed changed DSL artifact was not rejected")

        with tempfile.TemporaryDirectory(prefix="wellmanifest-dsl-outside-") as external:
            outside_manifest = Path(external) / MANIFEST_NAME
            outside_manifest.write_text(json.dumps(document), encoding="utf-8")
            linked_manifest = root / "linked-manifest.json"
            linked_manifest.symlink_to(outside_manifest)
            link_report, _ = validate_manifest(linked_manifest, root)
            if not link_report.has_code("DSL-PATH-001"):
                failures.append("manifest symlink escape was not rejected before reading")

    if failures:
        for failure in failures:
            print(f"SELFTEST FAIL: {failure}", file=sys.stderr)
        return 1
    print("SELFTEST PASS: valid, hash, LLM, path, symlink, and ownership cases")
    return 0


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
            normalized = safe_relative(raw, f"changed-file[{index}]", report, root / MANIFEST_NAME)
            if normalized is not None:
                changed.add(normalized)
    elif args.base:
        git_report, changed = git_paths(root, args.base, args.head, args.include_worktree)
        report.extend(git_report)
    else:
        report.error("DSL-GIT-001", "changes requires --base or at least one --changed-file", root)
    if not report.has_code("DSL-GIT-001"):
        report.extend(check_changed_paths(root, changed, manifests))
    print(report.render(args.format))
    return 1 if report.failed else 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate manifests and their bound artifacts")
    validate.add_argument("targets", nargs="*", help="manifest files or directories; default: repository root")
    validate.add_argument("--root", default=".", help="repository root")
    validate.add_argument("--format", choices=["text", "json"], default="text")
    validate.set_defaults(handler=command_validate)

    changes = subparsers.add_parser("changes", help="validate manifests and ownership of changed DSL files")
    changes.add_argument("--root", default=".", help="repository root")
    changes.add_argument("--base", help="accepted Git base revision")
    changes.add_argument("--head", default="HEAD", help="Git head revision")
    changes.add_argument("--include-worktree", action="store_true", help="also inspect staged, unstaged, and untracked files")
    changes.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="explicit repository-relative changed path; repeatable and usable in Git-free containers",
    )
    changes.add_argument("--format", choices=["text", "json"], default="text")
    changes.set_defaults(handler=command_changes)

    check = subparsers.add_parser("self-test", help="run dependency-free validator regression cases")
    check.set_defaults(handler=lambda _args: self_test())
    return result


def main() -> int:
    args = parser().parse_args()
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
