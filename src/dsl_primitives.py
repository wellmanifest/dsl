"""Shared constants, report primitives, and safe path/JSON helpers for dsl_check."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

MANIFEST_NAME = "dsl-manifest.json"
MANIFEST_SCHEMA = "wellmanifest.dsl/manifest/v1"
FINDINGS_SCHEMA = "wellmanifest.dsl/findings/v1"
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
COMMAND_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
FINDING_CODE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")
PRODUCER_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*[a-z0-9]$")

HELP_PAGE_SECTIONS = {
    "command": ("Purpose", "Syntax", "Inputs", "Outputs", "Errors", "Examples"),
    "error": ("Meaning", "Cause", "Resolution"),
    "critical": ("Risk", "Detection", "Remediation", "Verification"),
}


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

    def extend(self, other: Report) -> None:
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
            lines.append(
                f"{item.code} {item.severity.upper()}: {item.message}{location}"
            )
        errors = sum(item.severity == "error" for item in self.findings)
        lines.append(f"DSL-FAIL: failed ({errors} errors)")
        return "\n".join(lines)


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def strict_json_loads(raw: str) -> Any:
    return json.loads(raw, object_pairs_hook=_reject_duplicate_pairs)


def is_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def unique(values: list[Any]) -> bool:
    try:
        encoded = [
            json.dumps(value, sort_keys=True, separators=(",", ":")) for value in values
        ]
    except (TypeError, ValueError):
        return False
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
        report.error(
            "DSL-MANIFEST-001", f"{label} misses fields: {', '.join(missing)}", path
        )
    if unknown:
        report.error(
            "DSL-MANIFEST-001",
            f"{label} has unknown fields: {', '.join(unknown)}",
            path,
        )
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
        report.error(
            "DSL-MANIFEST-001", f"{label} must be an array of non-empty strings", path
        )
        return []
    if nonempty and not value:
        report.error("DSL-MANIFEST-001", f"{label} must not be empty", path)
    if not unique(value):
        report.error("DSL-MANIFEST-001", f"{label} contains duplicates", path)
    if allowed is not None:
        invalid = sorted(set(value) - allowed)
        if invalid:
            report.error(
                "DSL-MANIFEST-001",
                f"{label} has invalid values: {', '.join(invalid)}",
                path,
            )
    return value


def safe_relative(
    raw: Any, label: str, report: Report, manifest_path: Path
) -> str | None:
    if not is_string(raw):
        report.error(
            "DSL-PATH-001", f"{label} must be a non-empty relative path", manifest_path
        )
        return None
    if any(ord(ch) < 32 for ch in raw):
        report.error(
            "DSL-PATH-001",
            f"{label} must not contain control characters",
            manifest_path,
        )
        return None
    if "\\" in raw or re.match(r"^[A-Za-z]:", raw):
        report.error(
            "DSL-PATH-001",
            f"{label} must use repository-relative POSIX syntax",
            manifest_path,
        )
        return None
    candidate = PurePosixPath(raw)
    if candidate.is_absolute() or ".." in candidate.parts or raw in {".", ".."}:
        report.error(
            "DSL-PATH-001", f"{label} escapes the repository: {raw}", manifest_path
        )
        return None
    return raw


def resolve_repository_path(
    root: Path, raw: str, label: str, report: Report, manifest_path: Path
) -> Path | None:
    safe = safe_relative(raw, label, report, manifest_path)
    if safe is None:
        return None
    root_resolved = root.resolve()
    try:
        target = (root_resolved / safe).resolve(strict=False)
    except (OSError, RuntimeError) as error:
        report.error(
            "DSL-PATH-001", f"{label} cannot be resolved safely: {error}", manifest_path
        )
        return None
    try:
        target.relative_to(root_resolved)
    except ValueError:
        report.error(
            "DSL-PATH-001",
            f"{label} resolves outside the repository: {raw}",
            manifest_path,
        )
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
    if not is_string(value) or any(ch.isspace() or ord(ch) < 32 for ch in value):
        return False
    parsed = urlparse(value)
    return bool(parsed.scheme) and bool(parsed.netloc or parsed.path)


def help_page_text(name: str, kind: str) -> str:
    lines = [f"# {name}", ""]
    for heading in HELP_PAGE_SECTIONS[kind]:
        lines.extend([f"## {heading}", "Self-test content.", ""])
    return "\n".join(lines)


def write_example_help_pages(root: Path) -> dict[str, str]:
    pages = {
        "docs/DOCUMENT.md": help_page_text("DOCUMENT", "command"),
        "docs/VERSION.md": help_page_text("VERSION", "command"),
        "docs/ERROR/DSL-HASH-001.md": help_page_text("DSL-HASH-001", "error"),
        "docs/CRITICAL/SECURITY-001.md": help_page_text("SECURITY-001", "critical"),
    }
    digests: dict[str, str] = {}
    for relative, content in pages.items():
        page = root / relative
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(content, encoding="utf-8")
        digests[relative] = sha256(page)
    return digests
