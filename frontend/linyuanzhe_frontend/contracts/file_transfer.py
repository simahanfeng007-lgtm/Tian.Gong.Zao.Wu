from __future__ import annotations

"""L6.64 file transfer request contract.

The desktop frontend may prepare a sanitized file-transfer request for Runtime,
but it may not call tools, write memory, write audit records, apply rollback, or
expose raw local paths in reports. The current RC layer sends a metadata
handoff; any real file ingestion must be authorized and performed by
TiangongWangguan / Runtime.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Mapping
import hashlib
import mimetypes

def safe_text(value: Any, max_len: int = 260) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r", " ").replace("\n", " ").strip()
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def digest_text(value: Any, length: int = 16) -> str:
    data = ("" if value is None else str(value)).encode("utf-8", errors="ignore")
    return hashlib.sha256(data).hexdigest()[:length]

FILE_TRANSFER_CONTRACT_VERSION = "tiangong.l6_64.file_transfer_request.v1"
FILE_TRANSFER_ENDPOINT = "/files/transfer/request"
MAX_FILE_TRANSFER_BYTES = 512 * 1024 * 1024


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class FileTransferRequest:
    direction: str = "upload"
    file_name: str = ""
    size_bytes: int = 0
    sha256: str = ""
    mime_type: str = "application/octet-stream"
    purpose: str = "user_attachment"
    run_id: str = ""
    task_id: str = ""
    local_path_digest: str = ""
    runtime_handoff_path: str = ""
    frontend_contract: str = FILE_TRANSFER_CONTRACT_VERSION
    route_to_runtime_only: bool = True
    no_frontend_tool_execution: bool = True
    no_frontend_memory_write: bool = True
    no_frontend_audit_write: bool = True
    no_frontend_rollback_apply: bool = True
    no_frontend_path_exposure: bool = True
    raw_content_inline: bool = False

    @classmethod
    def from_path(
        cls,
        file_path: str | Path,
        *,
        purpose: str = "user_attachment",
        run_id: str = "",
        task_id: str = "",
    ) -> "FileTransferRequest":
        path = Path(file_path).expanduser()
        if not path.exists():
            raise FileNotFoundError("selected file does not exist")
        if not path.is_file():
            raise ValueError("selected path is not a file")
        size = path.stat().st_size
        if size > MAX_FILE_TRANSFER_BYTES:
            raise ValueError("selected file exceeds L6.64 transfer size limit")
        mime, _encoding = mimetypes.guess_type(path.name)
        return cls(
            file_name=safe_text(path.name, 160),
            size_bytes=int(size),
            sha256=_sha256_file(path),
            mime_type=safe_text(mime or "application/octet-stream", 100),
            purpose=safe_text(purpose, 120),
            run_id=safe_text(run_id, 80),
            task_id=safe_text(task_id, 80),
            local_path_digest=digest_text(str(path.resolve()), 16),
            runtime_handoff_path=str(path.resolve()),
        )

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)

    def to_public_record(self, *, status: str = "prepared", message: str = "") -> Dict[str, Any]:
        return {
            "frontend_contract": self.frontend_contract,
            "direction": self.direction,
            "file_name": self.file_name,
            "size_bytes": self.size_bytes,
            "sha256_digest": digest_text(self.sha256, 16),
            "mime_type": self.mime_type,
            "purpose": self.purpose,
            "status": safe_text(status, 80),
            "message": safe_text(message, 220),
            "route_to_runtime_only": True,
            "no_frontend_path_exposure": True,
        }


@dataclass(frozen=True)
class FileTransferPublicRecord:
    transfer_id: str = ""
    direction: str = "upload"
    file_name: str = ""
    size_bytes: int = 0
    sha256_digest: str = ""
    mime_type: str = "application/octet-stream"
    purpose: str = "user_attachment"
    status: str = "prepared"
    message: str = ""
    audit_id: str = ""
    frontend_only_fallback: bool = False
    route_to_runtime_only: bool = True
    no_frontend_path_exposure: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "FileTransferPublicRecord":
        payload = data.get("payload", data) if isinstance(data, Mapping) else {}
        if not isinstance(payload, Mapping):
            payload = {}
        return cls(
            transfer_id=safe_text(payload.get("transfer_id", payload.get("id", "")), 80),
            direction=safe_text(payload.get("direction", "upload"), 32),
            file_name=safe_text(payload.get("file_name", payload.get("filename", "")), 160),
            size_bytes=int(payload.get("size_bytes", 0) or 0),
            sha256_digest=safe_text(payload.get("sha256_digest", payload.get("sha256", "")), 32),
            mime_type=safe_text(payload.get("mime_type", "application/octet-stream"), 100),
            purpose=safe_text(payload.get("purpose", "user_attachment"), 120),
            status=safe_text(payload.get("status", "prepared"), 80),
            message=safe_text(payload.get("message", ""), 220),
            audit_id=safe_text(payload.get("audit_id", payload.get("audit_ref", "")), 80),
            frontend_only_fallback=bool(payload.get("frontend_only_fallback", False)),
            route_to_runtime_only=bool(payload.get("route_to_runtime_only", True)),
            no_frontend_path_exposure=bool(payload.get("no_frontend_path_exposure", True)),
        )

    @classmethod
    def from_request_result(
        cls,
        request: FileTransferRequest,
        *,
        status: str,
        message: str,
        transfer_id: str = "",
        audit_id: str = "",
        frontend_only_fallback: bool = False,
    ) -> "FileTransferPublicRecord":
        return cls(
            transfer_id=safe_text(transfer_id, 80),
            direction=request.direction,
            file_name=request.file_name,
            size_bytes=request.size_bytes,
            sha256_digest=digest_text(request.sha256, 16),
            mime_type=request.mime_type,
            purpose=request.purpose,
            status=safe_text(status, 80),
            message=safe_text(message, 220),
            audit_id=safe_text(audit_id, 80),
            frontend_only_fallback=frontend_only_fallback,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
