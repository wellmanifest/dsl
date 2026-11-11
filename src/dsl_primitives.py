"""Shared constants, report primitives, and safe path/URI helpers for dsl_check."""

from __future__ import annotations

import fnmatch
import json
import os
import re
import stat
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

from dsl_io import (
    MAX_HASH_BYTES,
    MAX_JSON_BYTES,
    MAX_JSON_DEPTH,
    MAX_JSON_INT_ABS,
    MAX_JSON_INT_DIGITS,
    _check_json_scalar,
    _enforce_json_depth,
    _has_forbidden_control_char,
    _has_symlink_ancestor,
    _is_valid_utf8,
    _open_regular_fd,
    _parse_bounded_int,
    _parse_finite_float,
    _reject_duplicate_pairs,
    _reject_nonfinite_constant,
    read_regular_bytes,
    read_regular_utf8,
    sha256,
    strict_json_loads,
)

MANIFEST_NAME = "dsl-manifest.json"
MANIFEST_SCHEMA = "wellmanifest.dsl/manifest/v1"
FINDINGS_SCHEMA = "wellmanifest.dsl/findings/v1"
SEMVER = re.compile(
    r"\A(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?\Z"
)
STABLE_ID = re.compile(r"\A[a-z0-9][a-z0-9._-]*[a-z0-9]\Z")
DIGEST = re.compile(r"\Asha256:([a-f0-9]{64})\Z")
REVISION = re.compile(r"\A[a-f0-9]{40}\Z")
DOMAIN = re.compile(r"\A[a-z0-9][a-z0-9._-]*\Z")
PREFIX = re.compile(r"\A[a-z][a-z0-9._-]*\Z")
MEDIA_TYPE = re.compile(r"\A[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+\Z")
COMMAND_NAME = re.compile(r"\A[A-Z][A-Z0-9_]*\Z")
FINDING_CODE = re.compile(r"\A[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\Z")
PRODUCER_ID = re.compile(r"\A[a-z0-9][a-z0-9._-]*[a-z0-9]\Z")
URI_SCHEME = re.compile(r"\A[a-zA-Z][a-zA-Z0-9+.-]*\Z")
WINDOWS_DRIVE_PREFIX = re.compile(r"\A[A-Za-z]:")

HELP_PAGE_SECTIONS = {
    "command": ("Purpose", "Syntax", "Inputs", "Outputs", "Errors", "Examples"),
    "error": ("Meaning", "Cause", "Resolution"),
    "critical": ("Risk", "Detection", "Remediation", "Verification"),
}

__all__ = [
    "COMMAND_NAME",
    "DIGEST",
    "DOMAIN",
    "FINDINGS_SCHEMA",
    "FINDING_CODE",
    "HELP_PAGE_SECTIONS",
    "MANIFEST_NAME",
    "MANIFEST_SCHEMA",
    "MAX_HASH_BYTES",
    "MAX_JSON_BYTES",
    "MAX_JSON_DEPTH",
    "MAX_JSON_INT_ABS",
    "MAX_JSON_INT_DIGITS",
    "MEDIA_TYPE",
    "PREFIX",
    "PRODUCER_ID",
    "REVISION",
    "SEMVER",
    "STABLE_ID",
    "URI_SCHEME",
    "WINDOWS_DRIVE_PREFIX",
    "Finding",
    "Report",
    "_check_json_scalar",
    "_enforce_json_depth",
    "_has_forbidden_control_char",
    "_has_symlink_ancestor",
    "_is_valid_utf8",
    "_open_regular_fd",
    "_parse_bounded_int",
    "_parse_finite_float",
    "_reject_duplicate_pairs",
    "_reject_nonfinite_constant",
    "check_object",
    "check_string_list",
    "help_page_text",
    "is_single_line_string",
    "is_string",
    "matches",
    "read_regular_bytes",
    "read_regular_utf8",
    "resolve_nonsymlink_under_root",
    "resolve_repository_path",
    "safe_relative",
    "sha256",
    "str_choice",
    "strict_json_loads",
    "string_set",
    "unique",
    "uri_is_valid",
    "write_example_help_pages",
]


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
                allow_nan=False,
            )
        if not self.findings:
            return "DSL-PASS: passed (0 errors)"
        lines = [
            f"{item.code} {item.severity.upper()}: {item.message}"
            + (f" [{item.path}]" if item.path else "")
            for item in self.findings
        ]
        errors = sum(item.severity == "error" for item in self.findings)
        lines.append(f"DSL-FAIL: failed ({errors} errors)")
        return "\n".join(lines)


def is_string(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and _is_valid_utf8(value)
        and not _has_forbidden_control_char(value, allow_whitespace=True)
    )


def is_single_line_string(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and _is_valid_utf8(value)
        and not _has_forbidden_control_char(value, allow_whitespace=False)
    )


def str_choice(value: Any, allowed: set[str] | frozenset[str]) -> bool:
    return isinstance(value, str) and value in allowed


def string_set(value: Any) -> set[str]:
    return (
        {item for item in value if isinstance(item, str)}
        if isinstance(value, list)
        else set()
    )


def unique(values: list[Any]) -> bool:
    try:
        encoded = [
            json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
            for value in values
        ]
    except (TypeError, ValueError, RecursionError, OverflowError):
        return False
    return len(encoded) == len(set(encoded))


def check_object(
    value: Any,
    required: set[str],
    allowed: set[str],
    label: str,
    report: Report,
    path: Path,
    *,
    code: str = "DSL-MANIFEST-001",
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        report.error(code, f"{label} must be an object", path)
        return None
    str_keys = {key for key in value if isinstance(key, str)}
    if len(str_keys) != len(value):
        report.error(code, f"{label} keys must all be strings", path)
        return None
    missing = sorted(required - str_keys)
    unknown = sorted(str_keys - allowed)
    if missing:
        report.error(code, f"{label} misses fields: {', '.join(missing)}", path)
    if unknown:
        report.error(code, f"{label} has unknown fields: {', '.join(unknown)}", path)
    return value


def check_string_list(
    value: Any,
    label: str,
    report: Report,
    path: Path,
    *,
    nonempty: bool = False,
    allowed: set[str] | None = None,
    single_line: bool = False,
) -> list[str]:
    predicate = is_single_line_string if single_line else is_string
    if not isinstance(value, list) or any(not predicate(item) for item in value):
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
    if not isinstance(raw, str) or not raw or not _is_valid_utf8(raw):
        report.error(
            "DSL-PATH-001", f"{label} must be a non-empty relative path", manifest_path
        )
        return None
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in raw):
        report.error(
            "DSL-PATH-001",
            f"{label} must not contain control characters",
            manifest_path,
        )
        return None
    if "\\" in raw or WINDOWS_DRIVE_PREFIX.match(raw):
        report.error(
            "DSL-PATH-001",
            f"{label} must use repository-relative POSIX syntax",
            manifest_path,
        )
        return None
    segments = raw.split("/")
    candidate = PurePosixPath(raw)
    if candidate.is_absolute() or ".." in segments or "." in segments or "" in segments:
        report.error(
            "DSL-PATH-001", f"{label} escapes the repository: {raw}", manifest_path
        )
        return None
    return raw


def resolve_nonsymlink_under_root(path: Path, root: Path) -> Path | None:
    try:
        if os.path.lexists(path) and stat.S_ISLNK(os.lstat(path).st_mode):
            return None
        root_resolved = root.resolve()
        candidate = path if path.is_absolute() else root / path
        try:
            rel = candidate.relative_to(root)
        except ValueError:
            rel = candidate.relative_to(root_resolved)
        if ".." in rel.parts:
            return None
        current = root_resolved
        for part in rel.parts:
            current = current / part
            try:
                st = os.lstat(current)
            except FileNotFoundError:
                break
            if stat.S_ISLNK(st.st_mode):
                return None
        current.resolve(strict=False).relative_to(root_resolved)
    except (OSError, RuntimeError, ValueError):
        return None
    return current


def resolve_repository_path(
    root: Path, raw: str, label: str, report: Report, manifest_path: Path
) -> Path | None:
    safe = safe_relative(raw, label, report, manifest_path)
    if safe is None:
        return None
    target = resolve_nonsymlink_under_root(root / safe, root)
    if target is None:
        report.error(
            "DSL-PATH-001",
            f"{label} resolves outside the repository or traverses a symlink: {raw}",
            manifest_path,
        )
        return None
    return target


def matches(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def uri_is_valid(value: Any) -> bool:
    if not is_single_line_string(value) or any(ch.isspace() for ch in value):
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    if URI_SCHEME.fullmatch(parsed.scheme) is None:
        return False
    has_authority_prefix = value[len(parsed.scheme) : len(parsed.scheme) + 3] == "://"
    scheme_lower = parsed.scheme.lower()
    if has_authority_prefix or scheme_lower in {"http", "https", "schema"}:
        if not parsed.netloc or parsed.hostname in {None, ".", ".."}:
            return False
        return not any(seg in {".", ".."} for seg in parsed.path.split("/"))
    opaque = parsed.netloc or parsed.path
    if not opaque:
        return False
    return not any(seg in {"", ".", ".."} for seg in re.split(r"[/:]", opaque))


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
