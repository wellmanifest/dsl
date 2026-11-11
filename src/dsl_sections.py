"""Core manifest section validators (owners, source, artifacts, semantics, LLM)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dsl_primitives import (
    DIGEST,
    MEDIA_TYPE,
    PREFIX,
    REVISION,
    Report,
    check_object,
    check_string_list,
    is_string,
    matches,
    resolve_repository_path,
    safe_relative,
    sha256,
    str_choice,
    unique,
    uri_is_valid,
)


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
        if not str_choice(
            item.get("kind"), {"repository", "organization", "team", "person"}
        ):
            report.error("DSL-MANIFEST-001", f"owners[{index}].kind is invalid", path)
        if not is_string(item.get("id")):
            report.error(
                "DSL-MANIFEST-001", f"owners[{index}].id must be non-empty", path
            )
        check_string_list(
            item.get("responsibilities"),
            f"owners[{index}].responsibilities",
            report,
            path,
            nonempty=True,
            allowed={"semantics", "validation", "compatibility", "runtime", "security"},
        )


def validate_source(
    value: Any, root: Path, report: Report, path: Path
) -> dict[str, Any] | None:
    required = {"repository", "path", "canonical", "mediaType", "selectors"}
    allowed = required | {"revision", "declaredVersion"}
    source = check_object(value, required, allowed, "source", report, path)
    if source is None:
        return None
    if not is_string(source.get("repository")):
        report.error("DSL-MANIFEST-001", "source.repository must be non-empty", path)
    source_path = source.get("path")
    if safe_relative(source_path, "source.path", report, path):
        resolved = resolve_repository_path(
            root, source_path, "source.path", report, path
        )
        if resolved is not None and not resolved.is_file():
            report.error(
                "DSL-PATH-002", f"source.path does not exist: {source_path}", path
            )
    revision = source.get("revision")
    if revision is not None and (
        not isinstance(revision, str) or REVISION.fullmatch(revision) is None
    ):
        report.error(
            "DSL-MANIFEST-001",
            "source.revision must be a 40-character lowercase Git SHA",
            path,
        )
    if "declaredVersion" in source and not is_string(source.get("declaredVersion")):
        report.error(
            "DSL-MANIFEST-001", "source.declaredVersion must be non-empty", path
        )
    if not str_choice(
        source.get("canonical"),
        {"json-ast", "protobuf", "text", "markdown-embedded", "other"},
    ):
        report.error("DSL-MANIFEST-001", "source.canonical is invalid", path)
    media_type = source.get("mediaType")
    if not isinstance(media_type, str) or MEDIA_TYPE.fullmatch(media_type) is None:
        report.error("DSL-MANIFEST-001", "source.mediaType is invalid", path)
    selectors = check_string_list(
        source.get("selectors"), "source.selectors", report, path
    )
    if source.get("canonical") == "markdown-embedded" and not selectors:
        report.error(
            "DSL-MANIFEST-001", "markdown-embedded sources require selectors", path
        )
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
        report.error(
            "DSL-MANIFEST-001", "artifacts must be a non-empty array", manifest_path
        )
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
        artifact_path = safe_relative(
            artifact.get("path"), f"artifacts[{index}].path", report, manifest_path
        )
        if artifact_path is None:
            continue
        if artifact_path in result:
            report.error(
                "DSL-MANIFEST-001",
                f"duplicate artifact path: {artifact_path}",
                manifest_path,
            )
            continue
        result[artifact_path] = artifact
        if not matches(artifact_path, owned_paths):
            report.error(
                "DSL-ARTIFACT-001",
                f"artifact is outside ownedPaths: {artifact_path}",
                manifest_path,
            )
        if not str_choice(
            artifact.get("role"),
            {
                "normative-source",
                "schema",
                "grammar",
                "parser-contract",
                "serializer-contract",
                "profile",
                "example",
                "documentation",
            },
        ):
            report.error(
                "DSL-MANIFEST-001",
                f"artifact role is invalid: {artifact.get('role')}",
                manifest_path,
            )
        digest = artifact.get("digest")
        if not isinstance(digest, str) or DIGEST.fullmatch(digest) is None:
            report.error(
                "DSL-HASH-002",
                f"artifact digest is invalid: {artifact_path}",
                manifest_path,
            )
        resolved = resolve_repository_path(
            root, artifact_path, f"artifact {artifact_path}", report, manifest_path
        )
        if resolved is None:
            continue
        if not resolved.is_file():
            report.error(
                "DSL-PATH-002",
                f"artifact does not exist: {artifact_path}",
                manifest_path,
            )
        elif isinstance(digest, str) and DIGEST.fullmatch(digest):
            try:
                observed_digest = sha256(resolved)
            except OSError as error:
                report.error(
                    "DSL-PATH-002",
                    f"artifact cannot be read: {artifact_path}: {error}",
                    manifest_path,
                )
            else:
                if observed_digest != digest:
                    report.error(
                        "DSL-HASH-001",
                        f"artifact digest is stale: {artifact_path}",
                        manifest_path,
                    )
    if source_path:
        source_artifact = result.get(source_path)
        if source_artifact is None or source_artifact.get("role") != "normative-source":
            report.error(
                "DSL-ARTIFACT-001",
                "source.path must be a normative-source artifact",
                manifest_path,
            )
    return result


def validate_namespaces(value: Any, report: Report, path: Path) -> None:
    if not isinstance(value, list) or not unique(value):
        report.error("DSL-MANIFEST-001", "namespaces must be a unique array", path)
        return
    prefixes: set[str] = set()
    for index, raw in enumerate(value):
        item = check_object(
            raw,
            {"prefix", "uri"},
            {"prefix", "uri"},
            f"namespaces[{index}]",
            report,
            path,
        )
        if item is None:
            continue
        prefix = item.get("prefix")
        if not isinstance(prefix, str) or PREFIX.fullmatch(prefix) is None:
            report.error(
                "DSL-MANIFEST-001", f"namespaces[{index}].prefix is invalid", path
            )
        elif prefix in prefixes:
            report.error(
                "DSL-MANIFEST-001", f"duplicate namespace prefix: {prefix}", path
            )
        prefixes.add(str(prefix))
        if not uri_is_valid(item.get("uri")):
            report.error(
                "DSL-MANIFEST-001", f"namespaces[{index}].uri is invalid", path
            )


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
            report.error(
                "DSL-MANIFEST-001",
                f"projections[{index}] names and media types must be non-empty",
                path,
            )
        if not str_choice(
            item.get("direction"),
            {"bidirectional", "from-canonical", "to-canonical"},
        ):
            report.error(
                "DSL-MANIFEST-001", f"projections[{index}].direction is invalid", path
            )
        if not isinstance(item.get("lossless"), bool):
            report.error(
                "DSL-MANIFEST-001",
                f"projections[{index}].lossless must be boolean",
                path,
            )


def validate_lifecycle(value: Any, status: Any, report: Report, path: Path) -> None:
    keys = {"compatibility", "stability", "breaking", "additive", "fix"}
    item = check_object(value, keys, keys, "lifecycle", report, path)
    if item is None:
        return
    expected = {
        "compatibility": "semver",
        "breaking": "major",
        "additive": "minor",
        "fix": "patch",
    }
    for key, expected_value in expected.items():
        if item.get(key) != expected_value:
            report.error(
                "DSL-COMPAT-001", f"lifecycle.{key} must equal {expected_value}", path
            )
    if not str_choice(item.get("stability"), {"experimental", "stable", "deprecated"}):
        report.error("DSL-MANIFEST-001", "lifecycle.stability is invalid", path)
    if item.get("stability") != status:
        report.error(
            "DSL-COMPAT-001", "status and lifecycle.stability must match", path
        )


def validate_semantics(value: Any, report: Report, path: Path) -> None:
    keys = {"effectModel", "unknownPolicy", "authoritySchema"}
    item = check_object(value, keys, keys, "semantics", report, path)
    if item is None:
        return
    effect = item.get("effectModel")
    if not str_choice(
        effect,
        {"descriptive", "declarative-policy", "propose-only", "controlled-effects"},
    ):
        report.error("DSL-MANIFEST-001", "semantics.effectModel is invalid", path)
    if not str_choice(
        item.get("unknownPolicy"), {"preserve", "reject", "domain-defined"}
    ):
        report.error("DSL-MANIFEST-001", "semantics.unknownPolicy is invalid", path)
    authority = item.get("authoritySchema")
    if effect == "controlled-effects" and not is_string(authority):
        report.error(
            "DSL-AUTH-001", "controlled-effects requires authoritySchema", path
        )
    if effect != "controlled-effects" and authority is not None:
        report.error(
            "DSL-AUTH-001",
            "authoritySchema is allowed only for controlled-effects",
            path,
        )


def validate_llm(value: Any, report: Report, path: Path) -> None:
    keys = {
        "mode",
        "requestSchemas",
        "responseSchemas",
        "naturalLanguage",
        "sourceSchema",
        "decisionProtocol",
        "modelAuthority",
        "strict",
    }
    item = check_object(value, keys, keys, "llm", report, path)
    if item is None:
        return
    mode = item.get("mode")
    if not str_choice(mode, {"none", "input", "output", "bidirectional"}):
        report.error("DSL-LLM-001", "llm.mode is invalid", path)
        mode = "invalid"
    requests = check_string_list(
        item.get("requestSchemas"), "llm.requestSchemas", report, path
    )
    responses = check_string_list(
        item.get("responseSchemas"), "llm.responseSchemas", report, path
    )
    if mode in {"input", "bidirectional"} and not requests:
        report.error("DSL-LLM-001", f"llm.mode={mode} requires requestSchemas", path)
    if mode in {"output", "bidirectional"} and not responses:
        report.error("DSL-LLM-001", f"llm.mode={mode} requires responseSchemas", path)
    if mode == "none" and (requests or responses):
        report.error(
            "DSL-LLM-001",
            "llm.mode=none forbids requestSchemas and responseSchemas",
            path,
        )
    natural = item.get("naturalLanguage")
    if not str_choice(natural, {"forbidden", "typed-source-only"}):
        report.error("DSL-LLM-001", "llm.naturalLanguage is invalid", path)
    source_schema = item.get("sourceSchema")
    if natural == "typed-source-only" and not is_string(source_schema):
        report.error("DSL-LLM-001", "typed-source-only requires sourceSchema", path)
    if natural == "forbidden" and source_schema is not None:
        report.error(
            "DSL-LLM-001", "forbidden natural language requires sourceSchema=null", path
        )
    protocol = item.get("decisionProtocol")
    if not str_choice(protocol, {"none", "dsl-input-output", "nl-to-dsl-input-output"}):
        report.error("DSL-LLM-001", "llm.decisionProtocol is invalid", path)
    elif mode == "none" and protocol != "none":
        report.error(
            "DSL-LLM-001", "llm.mode=none requires decisionProtocol=none", path
        )
    elif mode != "none":
        expected_protocol = (
            "nl-to-dsl-input-output"
            if natural == "typed-source-only"
            else "dsl-input-output"
        )
        if protocol != expected_protocol:
            report.error(
                "DSL-LLM-001",
                f"llm.decisionProtocol must equal {expected_protocol} for the declared naturalLanguage policy",
                path,
            )
        if mode != "bidirectional" or not requests or not responses:
            report.error(
                "DSL-LLM-001",
                "LLM decision boundaries require strict bidirectional requestSchemas and responseSchemas",
                path,
            )
    authority = item.get("modelAuthority")
    if mode == "none" and authority != "none":
        report.error("DSL-LLM-001", "llm.mode=none requires modelAuthority=none", path)
    if mode != "none" and authority != "propose-only":
        report.error(
            "DSL-LLM-001", "LLM-enabled DSLs require modelAuthority=propose-only", path
        )
    if item.get("strict") is not True:
        report.error("DSL-LLM-001", "llm.strict must be true", path)


def validate_conformance(value: Any, root: Path, report: Report, path: Path) -> None:
    keys = {"levels", "commands", "validExamples", "invalidExamples"}
    item = check_object(value, keys, keys, "conformance", report, path)
    if item is None:
        return
    check_string_list(
        item.get("levels"),
        "conformance.levels",
        report,
        path,
        nonempty=True,
        allowed={"manifest", "contract", "runtime", "llm-boundary"},
    )
    check_string_list(
        item.get("commands"), "conformance.commands", report, path, nonempty=True
    )
    for field in ("validExamples", "invalidExamples"):
        examples = check_string_list(
            item.get(field), f"conformance.{field}", report, path
        )
        for raw in examples:
            resolved = resolve_repository_path(
                root, raw, f"conformance.{field}", report, path
            )
            if resolved is not None and not resolved.is_file():
                report.error(
                    "DSL-CONFORMANCE-001", f"example does not exist: {raw}", path
                )


def validate_mappings(value: Any, report: Report, path: Path) -> None:
    if not isinstance(value, list) or not unique(value):
        report.error("DSL-MANIFEST-001", "mappings must be a unique array", path)
        return
    for index, raw in enumerate(value):
        required = {"standard", "version", "relation"}
        item = check_object(
            raw, required, required | {"uri"}, f"mappings[{index}]", report, path
        )
        if item is None:
            continue
        if not is_string(item.get("standard")) or not is_string(item.get("version")):
            report.error(
                "DSL-MANIFEST-001",
                f"mappings[{index}] names and versions must be non-empty",
                path,
            )
        if not str_choice(
            item.get("relation"),
            {"extends", "implements", "maps-to", "compatible-with"},
        ):
            report.error(
                "DSL-MANIFEST-001", f"mappings[{index}].relation is invalid", path
            )
        if "uri" in item and not uri_is_valid(item.get("uri")):
            report.error("DSL-MANIFEST-001", f"mappings[{index}].uri is invalid", path)
