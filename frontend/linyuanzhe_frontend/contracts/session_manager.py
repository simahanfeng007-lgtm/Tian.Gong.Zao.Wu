from __future__ import annotations

"""L6.67 multi-task Session Manager contract.

The desktop frontend may display task/session projections and submit resume/search
request envelopes to Runtime. It must not directly resume tools, mutate memory,
write audit records, apply rollback, or operate on another session outside the
Runtime / TiangongWangguan control path.
"""

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping

SESSION_MANAGER_CONTRACT_VERSION = "tiangong.l6_67.session_manager.v1"
SESSION_LIST_ENDPOINT = "/sessions/list"
SESSION_RESUME_ENDPOINT = "/sessions/resume"
SESSION_SEARCH_ENDPOINT = "/sessions/search"
SESSION_ARCHIVE_ENDPOINT = "/sessions/archive"

SESSION_STATUSES = {
    "running",
    "waiting_confirmation",
    "blocked",
    "recoverable",
    "completed",
    "failed",
    "paused",
    "queued",
}


def _safe_text(value: Any, max_len: int = 180) -> str:
    text = "" if value is None else str(value)
    for needle in ("api_key", "secret", "token", "password", "bearer", "mockkey_"):
        if needle in text.lower():
            text = "<redacted>"
            break
    text = text.replace("\r", " ").replace("\n", " ").strip()
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def _digest(value: Any, length: int = 16) -> str:
    text = "" if value is None else str(value)
    return sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:length] if text else ""


@dataclass(frozen=True)
class TaskSessionProjection:
    session_id_digest: str
    title: str
    status: str = "queued"
    current_stage: str = "等待 Runtime 投影"
    progress_percent: int = 0
    waiting_confirmation: bool = False
    blocked: bool = False
    recoverable: bool = False
    active: bool = False
    last_updated: str = "当前"
    run_id_digest: str = ""
    task_id_digest: str = ""
    audit_id: str = ""
    tags: List[str] = field(default_factory=list)
    message: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "TaskSessionProjection":
        status = _safe_text(data.get("status", "queued"), 60).lower() or "queued"
        if status not in SESSION_STATUSES:
            status = "queued"
        session_digest = data.get("session_id_digest") or data.get("session_digest")
        raw_session_id = data.get("session_id") or data.get("id") or data.get("title") or "session"
        run_digest = data.get("run_id_digest")
        raw_run_id = data.get("run_id") or ""
        task_digest = data.get("task_id_digest")
        raw_task_id = data.get("task_id") or ""
        return cls(
            session_id_digest=_safe_text(session_digest, 80) if session_digest else _digest(raw_session_id),
            title=_safe_text(data.get("title", data.get("name", "未命名任务")), 120),
            status=status,
            current_stage=_safe_text(data.get("current_stage", data.get("stage", "等待 Runtime 投影")), 140),
            progress_percent=max(0, min(100, int(data.get("progress_percent", data.get("progress", 0)) or 0))),
            waiting_confirmation=bool(data.get("waiting_confirmation", status == "waiting_confirmation")),
            blocked=bool(data.get("blocked", status == "blocked")),
            recoverable=bool(data.get("recoverable", status in {"recoverable", "failed", "paused", "blocked"})),
            active=bool(data.get("active", False)),
            last_updated=_safe_text(data.get("last_updated", "当前"), 80),
            run_id_digest=_safe_text(run_digest, 80) if run_digest else _digest(raw_run_id),
            task_id_digest=_safe_text(task_digest, 80) if task_digest else _digest(raw_task_id),
            audit_id=_safe_text(data.get("audit_id", data.get("audit_ref", "")), 80),
            tags=[_safe_text(x, 40) for x in data.get("tags", []) or []][:8],
            message=_safe_text(data.get("message", ""), 220),
        )


@dataclass(frozen=True)
class SessionResumeRequest:
    session_id_digest: str
    reason: str = "user_requested_resume"
    action: str = "resume"
    frontend_contract: str = SESSION_MANAGER_CONTRACT_VERSION
    route_to_runtime_only: bool = True
    no_frontend_execute: bool = True
    no_frontend_tool_execution: bool = True
    no_frontend_memory_write: bool = True
    no_frontend_audit_write: bool = True
    no_frontend_rollback_apply: bool = True

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SessionSearchRequest:
    query: str
    action: str = "search"
    frontend_contract: str = SESSION_MANAGER_CONTRACT_VERSION
    read_only_projection: bool = True
    no_frontend_execute: bool = True
    no_frontend_tool_execution: bool = True
    no_frontend_memory_write: bool = True
    no_frontend_audit_write: bool = True
    no_frontend_rollback_apply: bool = True

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SessionManagerStats:
    total: int = 0
    running: int = 0
    waiting_confirmation: int = 0
    blocked: int = 0
    recoverable: int = 0
    completed: int = 0
    failed: int = 0
    queued: int = 0

    @classmethod
    def from_sessions(cls, sessions: Iterable[TaskSessionProjection]) -> "SessionManagerStats":
        data = list(sessions)
        return cls(
            total=len(data),
            running=sum(1 for item in data if item.status == "running" or item.active),
            waiting_confirmation=sum(1 for item in data if item.waiting_confirmation or item.status == "waiting_confirmation"),
            blocked=sum(1 for item in data if item.blocked or item.status == "blocked"),
            recoverable=sum(1 for item in data if item.recoverable),
            completed=sum(1 for item in data if item.status == "completed"),
            failed=sum(1 for item in data if item.status == "failed"),
            queued=sum(1 for item in data if item.status == "queued"),
        )

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)
