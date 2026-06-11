"""L6.72.47 文件真实落盘提交与验真工具。"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any
from uuid import uuid4


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _fsync_parent_dir(path: Path) -> bool:
    try:
        flags = getattr(os, "O_RDONLY", 0)
        if hasattr(os, "O_DIRECTORY"):
            flags |= getattr(os, "O_DIRECTORY")
        fd = os.open(str(path), flags)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        return True
    except Exception:
        return False


def verify_file_commit(path: Path, *, expected_text: str | None = None, encoding: str = "utf-8") -> dict[str, Any]:
    exists = path.exists()
    is_file = path.is_file() if exists else False
    parent_entry_found = False
    try:
        parent_entry_found = any(child.name == path.name for child in path.parent.iterdir())
    except Exception:
        parent_entry_found = False
    byte_size = path.stat().st_size if exists and is_file else -1
    readback_matches = None
    readback_hash = ""
    if exists and is_file:
        raw = path.read_bytes()
        readback_hash = _sha256_bytes(raw)
        if expected_text is not None:
            try:
                readback_matches = path.read_text(encoding=encoding) == expected_text
            except Exception:
                readback_matches = False
    verified = bool(exists and is_file and parent_entry_found and (readback_matches is not False))
    return {
        "physical_commit_verified": verified,
        "exists": exists,
        "is_file": is_file,
        "parent_entry_found": parent_entry_found,
        "byte_size": byte_size,
        "readback_matches": readback_matches,
        "sha256": readback_hash,
    }


def write_text_atomic_verified(path: Path, content: str, *, encoding: str = "utf-8") -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp_{uuid4().hex[:12]}")
    encoded = content.encode(encoding, errors="strict")
    fsync_file_ok = False
    try:
        with temp.open("w", encoding=encoding, newline="") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
            fsync_file_ok = True
        os.replace(temp, path)
    finally:
        try:
            if temp.exists():
                temp.unlink()
        except Exception:
            pass
    fsync_parent_ok = _fsync_parent_dir(path.parent)
    verification = verify_file_commit(path, expected_text=content, encoding=encoding)
    verification.update({
        "atomic_replace": True,
        "fsync_file": fsync_file_ok,
        "fsync_parent": fsync_parent_ok,
        "expected_byte_size": len(encoded),
        "expected_sha256": _sha256_bytes(encoded),
    })
    if verification.get("byte_size") != len(encoded):
        verification["physical_commit_verified"] = False
    if verification.get("sha256") and verification.get("sha256") != verification.get("expected_sha256"):
        verification["physical_commit_verified"] = False
    return verification
