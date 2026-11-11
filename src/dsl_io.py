"""Bounded regular-file I/O, symlink-ancestor checks, and strict finite JSON parsing."""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from pathlib import Path
from typing import Any

MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_JSON_DEPTH = 64
MAX_JSON_INT_DIGITS = 400
MAX_JSON_INT_ABS = 10**MAX_JSON_INT_DIGITS - 1
MAX_HASH_BYTES = 64 * 1024 * 1024


def _is_valid_utf8(value: str) -> bool:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _has_forbidden_control_char(value: str, *, allow_whitespace: bool = True) -> bool:
    for ch in value:
        code = ord(ch)
        if code == 127:
            return True
        if code < 32 and (not allow_whitespace or ch not in {"\n", "\t"}):
            return True
    return False


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


def _parse_bounded_int(token: str) -> int:
    digits = token[1:] if token.startswith(("+", "-")) else token
    if len(digits) > MAX_JSON_INT_DIGITS:
        raise ValueError("JSON integer exceeds maximum safe digit count")
    parsed = int(token)
    if abs(parsed) > MAX_JSON_INT_ABS:
        raise ValueError("JSON integer exceeds safe magnitude")
    return parsed


def _check_json_scalar(value: Any) -> None:
    if isinstance(value, str) and not _is_valid_utf8(value):
        raise ValueError("JSON string contains invalid UTF-8 surrogate")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite float in JSON structure")
    if (
        isinstance(value, int)
        and not isinstance(value, bool)
        and abs(value) > MAX_JSON_INT_ABS
    ):
        raise ValueError("JSON integer exceeds safe magnitude")


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
                if not _is_valid_utf8(key):
                    raise ValueError("JSON key contains invalid UTF-8 surrogate")
                if isinstance(child, (dict, list)):
                    stack.append((child, depth + 1))
                else:
                    _check_json_scalar(child)
        elif isinstance(current, list):
            for child in current:
                if isinstance(child, (dict, list)):
                    stack.append((child, depth + 1))
                else:
                    _check_json_scalar(child)
        else:
            _check_json_scalar(current)


def _has_symlink_ancestor(path: Path) -> bool:
    raw = os.fspath(path)
    raw_parts = Path(raw).parts
    start_idx = 3 if os.path.isabs(raw) else 1
    for idx in range(start_idx, len(raw_parts)):
        prefix = Path(*raw_parts[:idx])
        if prefix.parts and all(part in {".", ".."} for part in prefix.parts):
            continue
        try:
            if stat.S_ISLNK(os.lstat(prefix).st_mode):
                return True
        except FileNotFoundError:
            break
        except OSError:
            return True
    normalized = Path(os.path.abspath(raw))
    for anc in normalized.parents:
        if len(anc.parts) <= 2:
            continue
        try:
            if stat.S_ISLNK(os.lstat(anc).st_mode):
                return True
        except FileNotFoundError:
            continue
        except OSError:
            return True
    return False


def _open_regular_fd(
    path: Path | str, *, follow_symlinks: bool = False
) -> tuple[int, int]:
    target = Path(path)
    if not follow_symlinks and _has_symlink_ancestor(target):
        raise OSError(f"refusing to traverse symlink ancestor: {target}")
    link_meta = None if follow_symlinks else os.lstat(target)
    if link_meta is not None and stat.S_ISLNK(link_meta.st_mode):
        raise OSError(f"refusing to open symlink: {target}")
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
    if not follow_symlinks:
        flags |= getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(target, flags)
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise OSError(f"not a regular file: {target}")
        if link_meta is not None and (
            metadata.st_dev != link_meta.st_dev or metadata.st_ino != link_meta.st_ino
        ):
            raise OSError(f"inode changed during open: {target}")
    except BaseException:
        os.close(fd)
        raise
    return fd, metadata.st_size


def read_regular_bytes(
    path: Path | str,
    *,
    max_bytes: int = MAX_JSON_BYTES,
    follow_symlinks: bool = False,
) -> bytes:
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
        raise ValueError("max_bytes must be a positive integer")
    fd, st_size = _open_regular_fd(path, follow_symlinks=follow_symlinks)
    try:
        if st_size > max_bytes:
            raise ValueError(
                f"file exceeds maximum allowed size ({max_bytes} bytes): {path}"
            )
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, min(65536, max_bytes + 1 - total))
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
    path: Path | str,
    *,
    max_bytes: int = MAX_JSON_BYTES,
    follow_symlinks: bool = False,
) -> str:
    return read_regular_bytes(
        path, max_bytes=max_bytes, follow_symlinks=follow_symlinks
    ).decode("utf-8")


def strict_json_loads(raw: str) -> Any:
    if not isinstance(raw, str):
        raise TypeError("JSON input must be a string")
    if not _is_valid_utf8(raw):
        raise ValueError("JSON input contains invalid UTF-8 surrogate")
    if len(raw.encode("utf-8")) > MAX_JSON_BYTES:
        raise ValueError(f"JSON input exceeds {MAX_JSON_BYTES} bytes")
    try:
        parsed = json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_nonfinite_constant,
            parse_float=_parse_finite_float,
            parse_int=_parse_bounded_int,
        )
    except RecursionError as error:
        raise ValueError("JSON nesting exceeds maximum depth") from error
    _enforce_json_depth(parsed, MAX_JSON_DEPTH)
    return parsed


def sha256(path: Path | str) -> str:
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
