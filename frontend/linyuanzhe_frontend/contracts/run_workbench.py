from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Mapping

import re


_SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|private[_-]?key)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)(mockkey_[A-Za-z0-9_\-]{8,})"),
    re.compile(r"(?i)(bearer\s+[A-Za-z0-9_\-.]+)"),
    re.compile(r"([A-Za-z]:\\[^\n\r\t]+)"),
    re.compile(r"(/(?:home|Users|mnt|var|etc)/[^\n\r\t]+)"),
]


def safe_text(value: Any, max_len: int = 260) -> str:
    text = "" if value is None else str(value)
    for pattern in _SENSITIVE_PATTERNS:
        text = pattern.sub("<redacted>", text)
    text = text.replace("\r", " ").replace("\n", " ").strip()
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text

RUN_WORKBENCH_CONTRACT_VERSION = "tiangong.l6_72_27.desktop_run_workbench.v1"

RUN_STATE_LABELS = {
    "idle": "待机",
    "submitting": "提交中",
    "accepted": "已接收",
    "planning": "规划中",
    "waiting_approval": "等待审批",
    "tool_running": "工具运行中",
    "streaming": "结果回传中",
    "reconnecting": "断线续接中",
    "completed": "已完成",
    "failed": "失败",
    "cancelled": "已取消",
    "recoverable": "可恢复",
}

TERMINAL_STATES = {"completed", "failed", "cancelled"}
ACTIVE_STATES = {"submitting", "accepted", "planning", "waiting_approval", "tool_running", "streaming", "reconnecting"}


def normalize_run_state(value: Any) -> str:
    clean = safe_text(value or "idle", 40).lower().replace("-", "_")
    aliases = {
        "running": "tool_running",
        "queued": "accepted",
        "waiting_confirmation": "waiting_approval",
        "approval_required": "waiting_approval",
        "error": "failed",
        "interrupted": "recoverable",
        "partial_or_failed": "recoverable",
        "failed_recoverable": "recoverable",
        "partial_with_resume": "recoverable",
        "provider_not_ready": "recoverable",
        "model_required": "recoverable",
        "done": "completed",
        "ok": "completed",
        "completed_pass": "completed",
        "completed_with_warnings": "completed",
        "deterministic_fallback": "completed",
    }
    clean = aliases.get(clean, clean)
    return clean if clean in RUN_STATE_LABELS else "idle"


def run_state_label(value: Any) -> str:
    return RUN_STATE_LABELS.get(normalize_run_state(value), "待机")


@dataclass
class RunWorkbenchProjection:
    contract_version: str = RUN_WORKBENCH_CONTRACT_VERSION
    state: str = "idle"
    label: str = "待机"
    run_id: str = ""
    task_id: str = ""
    frontend_work_mode: str = "work"
    planner_mode: str = "model_suggest"
    current_tool_name: str = ""
    current_tool_status: str = ""
    waiting_ticket_id: str = ""
    heartbeat_count: int = 0
    heartbeat_age_ms: int = 0
    last_event: str = ""
    last_event_at: str = ""
    diagnostic_summary: str = ""
    reconnect_available: bool = False
    resume_available: bool = False
    stop_available: bool = False
    frontend_executes_tools: bool = False

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RunWorkbenchProjection":
        state = normalize_run_state(data.get("state", data.get("run_state", "idle")))
        return cls(
            state=state,
            label=safe_text(data.get("label") or run_state_label(state), 40),
            run_id=safe_text(data.get("run_id", ""), 80),
            task_id=safe_text(data.get("task_id", ""), 80),
            frontend_work_mode=safe_text(data.get("frontend_work_mode", "work"), 40),
            planner_mode=safe_text(data.get("planner_mode", "model_suggest"), 40),
            current_tool_name=safe_text(data.get("current_tool_name", ""), 80),
            current_tool_status=safe_text(data.get("current_tool_status", ""), 80),
            waiting_ticket_id=safe_text(data.get("waiting_ticket_id", ""), 80),
            heartbeat_count=int(data.get("heartbeat_count", 0) or 0),
            heartbeat_age_ms=int(data.get("heartbeat_age_ms", 0) or 0),
            last_event=safe_text(data.get("last_event", ""), 80),
            last_event_at=safe_text(data.get("last_event_at", ""), 80),
            diagnostic_summary=safe_text(data.get("diagnostic_summary", ""), 260),
            reconnect_available=bool(data.get("reconnect_available", state in {"reconnecting", "recoverable", "failed"})),
            resume_available=bool(data.get("resume_available", state in {"reconnecting", "recoverable"})),
            stop_available=bool(data.get("stop_available", state in ACTIVE_STATES)),
            frontend_executes_tools=False,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
