"""Shared constants, report primitives, and safe path/JSON helpers for dsl_check."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import math
import os
import re
import stat
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_JSON_DEPTH = 64
MAX_HASH_BYTES = 64 * 1024 * 1024

MANIFEST_NAME = "dsl-manifest.json"
MANIFEST_SCHEMA = "wellmanifest.dsl/manifest/v1"
FINDINGS_SCHEMA = "wellmanifest.dsl/findings/v1"
SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?\Z"
)
STABLE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*[a-z0-9]\Z")
DIGEST = re.compile(r"^sha256:([a-f0-9]{64})\Z")
REVISION = re.compile(r"^[a-f0-9]{40}\Z")
DOMAIN = re.compile(r"^[a-z0-9][a-z0-9._-]*\Z")
PREFIX = re.compile(r"^[a-z][a-z0-9._-]*\Z")
MEDIA_TYPE = re.compile(r"^[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+\Z")
COMMAND_NAME = re.compile(r"^[A-Z][A-Z0-9_]*\Z")
FINDING_CODE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\Z")
PRODUCER_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*[a-z0-9]\Z")
URI_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*\Z")

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


def _reject_nonfinite_constant(token: str) -> Any:
    raise ValueError(f"non-finite JSON constant is forbidden: {token}")


def _parse_finite_float(token: str) -> float:
    parsed = float(token)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON number overflows finite float range: {token}")
    return parsed


def _enforce_json_depth(root_value: Any, max_depth: int = MAX_JSON_DEPTH) -> None:
    stack: list[tuple[Any, int]] = [(root_value, 0)]
    while stack:
        current, depth = stack.pop()
        if depth > max_depth:
            raise ValueError(f"JSON nesting exceeds maximum depth of {max_depth}")
        if isinstance(current, dict):
            for key, child in current.items():
                if not isinstance(key, str):
                    raise TypeError("JSON object keys must be strings")
                if isinstance(child, float) and not math.isfinite(child):
                    raise ValueError("non-finite float in JSON structure")
                if isinstance(child, (dict, list)):
                    stack.append((child, depth + 1))
        elif isinstance(current, list):
            for child in current:
                if isinstance(child, float) and not math.isfinite(child):
                    raise ValueError("non-finite float in JSON structure")
                if isinstance(child, (dict, list)):
                    stack.append((child, depth + 1))
        elif isinstance(current, float) and not math.isfinite(current):
            raise ValueError("non-finite float in JSON structure")


def _open_regular_fd(path: Path, *, follow_symlinks: bool = False) -> tuple[int, int]:
    link_meta = None if follow_symlinks else os.lstat(path)
    if link_meta is not None and stat.S_ISLNK(link_meta.st_mode):
        raise OSError(f"refusing to open symlink: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
    if not follow_symlinks:
        flags |= getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise OSError(f"not a regular file: {path}")
        if link_meta is not None and (
            metadata.st_dev != link_meta.st_dev or metadata.st_ino != link_meta.st_ino
        ):
            raise OSError(f"inode changed during open: {path}")
    except BaseException:
        os.close(fd)
        raise
    return fd, metadata.st_size


def read_regular_bytes(
    path: Path, *, max_bytes: int = MAX_JSON_BYTES, follow_symlinks: bool = False
) -> bytes:
    fd, st_size = _open_regular_fd(path, follow_symlinks=follow_symlinks)
    try:
        if st_size > max_bytes:
            raise ValueError(
                f"file exceeds maximum allowed size ({max_bytes} bytes): {path}"
            )
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(
                    f"file exceeds maximum allowed size ({max_bytes} bytes): {path}"
                )
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def read_regular_utf8(
    path: Path, *, max_bytes: int = MAX_JSON_BYTES, follow_symlinks: bool = False
) -> str:
    return read_regular_bytes(
        path, max_bytes=max_bytes, follow_symlinks=follow_symlinks
    ).decode("utf-8")


def strict_json_loads(raw: str) -> Any:
    if not isinstance(raw, str):
        raise TypeError("JSON input must be a string")
    if len(raw.encode("utf-8")) > MAX_JSON_BYTES:
        raise ValueError(f"JSON input exceeds {MAX_JSON_BYTES} bytes")
    try:
        parsed = json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_nonfinite_constant,
            parse_float=_parse_finite_float,
        )
    except RecursionError as error:
        raise ValueError("JSON nesting exceeds maximum depth") from error
    _enforce_json_depth(parsed, MAX_JSON_DEPTH)
    return parsed


def is_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


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
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in raw):
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


def sha256(path: Path) -> str:
    fd, st_size = _open_regular_fd(path, follow_symlinks=False)
    try:
        if st_size > MAX_HASH_BYTES:
            raise OSError(
                f"file exceeds maximum hash size ({MAX_HASH_BYTES} bytes): {path}"
            )
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_HASH_BYTES:
                raise OSError(
                    f"file exceeds maximum hash size ({MAX_HASH_BYTES} bytes): {path}"
                )
            digest.update(chunk)
        return f"sha256:{digest.hexdigest()}"
    finally:
        os.close(fd)


def uri_is_valid(value: Any) -> bool:
    if not is_string(value) or any(
        ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in value
    ):
        return False
    parsed = urlparse(value)
    if URI_SCHEME.fullmatch(parsed.scheme) is None:
        return False
    has_authority_prefix = value[len(parsed.scheme) : len(parsed.scheme) + 3] == "://"
    scheme_lower = parsed.scheme.lower()
    no_dotdot = ".." not in re.split(r"[/:]", parsed.path)
    if has_authority_prefix or scheme_lower in {"http", "https", "schema"}:
        return bool(parsed.netloc) and no_dotdot
    return bool(parsed.netloc or parsed.path) and no_dotdot


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
