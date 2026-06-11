from __future__ import annotations

"""L6.65 Agent Workspace / sandbox and file authorization contract.

The desktop frontend may display workspace policy and submit sanitized
workspace/file authorization requests to Runtime. It must not create sandbox
accounts, mutate workspace ACLs, copy file bytes, expose raw local paths, write
audit records, or apply rollback locally.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping
import hashlib

WORKSPACE_CONTRACT_VERSION = "tiangong.l6_65.agent_workspace.v1"
WORKSPACE_POLICY_ENDPOINT = "/workspace/policy"
FILE_AUTHORIZATION_ENDPOINT = "/workspace/file/authorize"
DOWNLOAD_CLAIM_ENDPOINT = "/files/download/claim"
ALLOWED_WORKSPACE_MODES = ("read", "write", "read_write", "download")
ALLOWED_WORKSPACE_SCOPES = ("user_selected_file", "workspace_inbox", "workspace_outbox", "artifact_download", "temporary_handoff")
MAX_AUTH_RECORDS = 40


def safe_text(value: Any, max_len: int = 260) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r", " ").replace("\n", " ").strip()
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def digest_text(value: Any, length: int = 16) -> str:
    data = ("" if value is None else str(value)).encode("utf-8", errors="ignore")
    return hashlib.sha256(data).hexdigest()[:length]


def _workspace_name_from_path(path: str | Path) -> str:
    p = Path(path).expanduser()
    return safe_text(p.name or "selected_file", 160)


@dataclass(frozen=True)
class WorkspaceMount:
    name: str = "agent_workspace"
    scope: str = "temporary_handoff"
    mode: str = "read"
    path_digest: str = ""
    writable: bool = False
    runtime_owned: bool = True
    user_visible: bool = True
    expires_hint: str = "per_run"

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "WorkspaceMount":
        return cls(
            name=safe_text(data.get("name", "agent_workspace"), 100),
            scope=safe_text(data.get("scope", "temporary_handoff"), 80),
            mode=safe_text(data.get("mode", "read"), 32),
            path_digest=safe_text(data.get("path_digest", ""), 32),
            writable=bool(data.get("writable", False)),
            runtime_owned=bool(data.get("runtime_owned", True)),
            user_visible=bool(data.get("user_visible", True)),
            expires_hint=safe_text(data.get("expires_hint", "per_run"), 80),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkspacePolicyProjection:
    workspace_id_digest: str = ""
    root_digest: str = ""
    default_mode: str = "read"
    allow_write_requires_confirmation: bool = True
    allowed_scopes: List[str] = field(default_factory=lambda: list(ALLOWED_WORKSPACE_SCOPES))
    max_upload_bytes: int = 512 * 1024 * 1024
    raw_path_visible: bool = False
    frontend_may_create_workspace: bool = False
    frontend_may_mutate_acl: bool = False
    frontend_may_copy_file_bytes: bool = False
    runtime_authority_required: bool = True
    mounts: List[WorkspaceMount] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "WorkspacePolicyProjection":
        mounts = [WorkspaceMount.from_mapping(x) for x in data.get("mounts", []) or [] if isinstance(x, Mapping)]
        return cls(
            workspace_id_digest=safe_text(data.get("workspace_id_digest", data.get("workspace_id", "")), 32),
            root_digest=safe_text(data.get("root_digest", ""), 32),
            default_mode=safe_text(data.get("default_mode", "read"), 32),
            allow_write_requires_confirmation=bool(data.get("allow_write_requires_confirmation", True)),
            allowed_scopes=[safe_text(x, 80) for x in data.get("allowed_scopes", list(ALLOWED_WORKSPACE_SCOPES)) or []],
            max_upload_bytes=int(data.get("max_upload_bytes", 512 * 1024 * 1024) or 0),
            raw_path_visible=bool(data.get("raw_path_visible", False)),
            frontend_may_create_workspace=bool(data.get("frontend_may_create_workspace", False)),
            frontend_may_mutate_acl=bool(data.get("frontend_may_mutate_acl", False)),
            frontend_may_copy_file_bytes=bool(data.get("frontend_may_copy_file_bytes", False)),
            runtime_authority_required=bool(data.get("runtime_authority_required", True)),
            mounts=mounts,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FileAuthorizationRequest:
    file_name: str = ""
    mode: str = "read"
    scope: str = "user_selected_file"
    purpose: str = "user_attachment"
    run_id: str = ""
    task_id: str = ""
    local_path_digest: str = ""
    frontend_contract: str = WORKSPACE_CONTRACT_VERSION
    route_to_runtime_only: bool = True
    no_frontend_workspace_create: bool = True
    no_frontend_acl_mutation: bool = True
    no_frontend_file_copy: bool = True
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
        mode: str = "read",
        scope: str = "user_selected_file",
        purpose: str = "user_attachment",
        run_id: str = "",
        task_id: str = "",
    ) -> "FileAuthorizationRequest":
        mode_norm = safe_text(mode, 32).lower() or "read"
        scope_norm = safe_text(scope, 80) or "user_selected_file"
        if mode_norm not in ALLOWED_WORKSPACE_MODES:
            raise ValueError("unsupported workspace file authorization mode")
        if scope_norm not in ALLOWED_WORKSPACE_SCOPES:
            raise ValueError("unsupported workspace authorization scope")
        p = Path(file_path).expanduser()
        return cls(
            file_name=_workspace_name_from_path(p),
            mode=mode_norm,
            scope=scope_norm,
            purpose=safe_text(purpose, 120),
            run_id=safe_text(run_id, 80),
            task_id=safe_text(task_id, 80),
            local_path_digest=digest_text(str(p.resolve()), 16),
        )

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FileAuthorizationPublicRecord:
    authorization_id: str = ""
    file_name: str = ""
    mode: str = "read"
    scope: str = "user_selected_file"
    purpose: str = "user_attachment"
    status: str = "prepared"
    message: str = ""
    audit_id: str = ""
    path_digest: str = ""
    runtime_workspace_digest: str = ""
    frontend_only_fallback: bool = False
    raw_path_visible: bool = False
    route_to_runtime_only: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "FileAuthorizationPublicRecord":
        payload = data.get("payload", data) if isinstance(data, Mapping) else {}
        if not isinstance(payload, Mapping):
            payload = {}
        return cls(
            authorization_id=safe_text(payload.get("authorization_id", payload.get("id", "")), 80),
            file_name=safe_text(payload.get("file_name", payload.get("filename", "")), 160),
            mode=safe_text(payload.get("mode", "read"), 32),
            scope=safe_text(payload.get("scope", "user_selected_file"), 80),
            purpose=safe_text(payload.get("purpose", "user_attachment"), 120),
            status=safe_text(payload.get("status", "prepared"), 80),
            message=safe_text(payload.get("message", ""), 220),
            audit_id=safe_text(payload.get("audit_id", payload.get("audit_ref", "")), 80),
            path_digest=safe_text(payload.get("path_digest", payload.get("local_path_digest", "")), 32),
            runtime_workspace_digest=safe_text(payload.get("runtime_workspace_digest", payload.get("workspace_digest", "")), 32),
            frontend_only_fallback=bool(payload.get("frontend_only_fallback", False)),
            raw_path_visible=bool(payload.get("raw_path_visible", False)),
            route_to_runtime_only=bool(payload.get("route_to_runtime_only", True)),
        )

    @classmethod
    def from_request_result(
        cls,
        request: FileAuthorizationRequest,
        *,
        status: str,
        message: str,
        authorization_id: str = "",
        audit_id: str = "",
        runtime_workspace_digest: str = "",
        frontend_only_fallback: bool = False,
    ) -> "FileAuthorizationPublicRecord":
        return cls(
            authorization_id=safe_text(authorization_id, 80),
            file_name=request.file_name,
            mode=request.mode,
            scope=request.scope,
            purpose=request.purpose,
            status=safe_text(status, 80),
            message=safe_text(message, 220),
            audit_id=safe_text(audit_id, 80),
            path_digest=request.local_path_digest,
            runtime_workspace_digest=safe_text(runtime_workspace_digest, 32),
            frontend_only_fallback=frontend_only_fallback,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DownloadHandoffRecord:
    artifact_id_digest: str = ""
    file_name: str = ""
    status: str = "ready"
    message: str = ""
    download_token_digest: str = ""
    expires_hint: str = "per_run"
    audit_id: str = ""
    frontend_only_fallback: bool = False
    no_raw_download_token_display: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "DownloadHandoffRecord":
        payload = data.get("payload", data) if isinstance(data, Mapping) else {}
        if not isinstance(payload, Mapping):
            payload = {}
        raw_token = payload.get("download_token", payload.get("token", ""))
        return cls(
            artifact_id_digest=safe_text(payload.get("artifact_id_digest", digest_text(payload.get("artifact_id", ""))), 32),
            file_name=safe_text(payload.get("file_name", payload.get("filename", "")), 160),
            status=safe_text(payload.get("status", "ready"), 80),
            message=safe_text(payload.get("message", ""), 220),
            download_token_digest=safe_text(payload.get("download_token_digest", digest_text(raw_token)), 32),
            expires_hint=safe_text(payload.get("expires_hint", "per_run"), 80),
            audit_id=safe_text(payload.get("audit_id", payload.get("audit_ref", "")), 80),
            frontend_only_fallback=bool(payload.get("frontend_only_fallback", False)),
            no_raw_download_token_display=bool(payload.get("no_raw_download_token_display", True)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def workspace_policy() -> Dict[str, Any]:
    return {
        "contract_version": WORKSPACE_CONTRACT_VERSION,
        "frontend_role": "display_and_request_only",
        "runtime_authority_required": True,
        "allowed_modes": list(ALLOWED_WORKSPACE_MODES),
        "allowed_scopes": list(ALLOWED_WORKSPACE_SCOPES),
        "forbidden": [
            "frontend_create_workspace",
            "frontend_mutate_acl",
            "frontend_copy_file_bytes",
            "frontend_show_raw_path",
            "frontend_write_memory",
            "frontend_write_audit",
            "frontend_apply_rollback",
        ],
    }
