from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional
import json
import re

from .runtime_snapshot import digest_text, safe_text


SSE_CONTRACT_VERSION = "tiangong.l6_72_27.frontend_sse_run_workbench.v1"
CHAT_STREAM_ENDPOINT = "/chat/stream-events"
HEALTH_ENDPOINT = "/health/runtime"
PROVIDER_SETTINGS_ENDPOINT = "/settings/provider"
PRODUCT_METADATA_ENDPOINT = "/metadata/product"

SSE_EVENT_TYPES = {
    "run_started",
    "run_accepted",
    "planner_started",
    "planner_plan",
    "runtime_state",
    "heartbeat",
    "quality_gate",
    "approval_required",
    "tool_started",
    "tool_progress",
    "tool_result",
    "execution_report",
    "audit_event",
    "rollback_ticket",
    "rollback_event",
    "assistant_delta",
    "assistant_final",
    "run_terminal",
    "error",
}
TERMINAL_EVENT_ORDER = ("assistant_final", "run_terminal")
STATUS_BAR_FIELDS = (
    "runtime_status",
    "provider_model",
    "budget_pool",
    "budget_used_ratio",
    "gate_status",
    "audit_id",
    "memory_mode",
    "tools_allowed",
    "latency_ms",
)
SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "token",
    "secret",
    "password",
    "passwd",
    "private_key",
    "base_url",
    "endpoint",
    "endpoint_url",
    "provider_base_url",
}
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-.]+"),
    re.compile(r"(?i)mockkey_[A-Za-z0-9_\-]{8,}"),
]


@dataclass(frozen=True)
class RuntimeSseEvent:
    event: str
    seq: int = 0
    run_id: str = ""
    task_id: str = ""
    timestamp: str = ""
    display_channel: str = ""
    visibility: str = ""
    event_kind: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any], *, event_hint: str = "") -> "RuntimeSseEvent":
        event = safe_text(data.get("event") or event_hint or "message", 64)
        payload = data.get("payload")
        routing_keys = {"event", "seq", "run_id", "task_id", "timestamp", "display_channel", "visibility", "event_kind"}
        if payload is None:
            payload = {k: v for k, v in data.items() if k not in routing_keys}
        if not isinstance(payload, Mapping):
            payload = {"value": payload}
        payload = dict(payload)
        display_channel, visibility, event_kind = _normalize_event_route(
            event,
            display_channel=data.get("display_channel") or payload.get("display_channel"),
            visibility=data.get("visibility") or payload.get("visibility"),
            event_kind=data.get("event_kind") or payload.get("event_kind"),
        )
        payload.setdefault("display_channel", display_channel)
        payload.setdefault("visibility", visibility)
        payload.setdefault("event_kind", event_kind)
        return cls(
            event=event,
            seq=_safe_int(data.get("seq"), 0),
            run_id=safe_text(data.get("run_id", ""), 80),
            task_id=safe_text(data.get("task_id", ""), 80),
            timestamp=safe_text(data.get("timestamp", ""), 80),
            display_channel=display_channel,
            visibility=visibility,
            event_kind=event_kind,
            payload=sanitize_event_payload(payload),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event,
            "seq": self.seq,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "display_channel": self.display_channel,
            "visibility": self.visibility,
            "event_kind": self.event_kind,
            "payload": self.payload,
        }


def _normalize_event_route(event: str, *, display_channel: Any = "", visibility: Any = "", event_kind: Any = "") -> tuple[str, str, str]:
    channel = safe_text(display_channel, 40) or ""
    visible = safe_text(visibility, 40) or ""
    kind = safe_text(event_kind, 40) or ""
    if not channel:
        if event in {"assistant_delta", "assistant_final", "approval_required"}:
            channel = "conversation"
        elif event in {"audit_event"}:
            channel = "silent_audit"
        elif event in {"run_started", "planner_started", "runtime_state", "run_terminal"}:
            channel = "status"
        else:
            channel = "workbench"
    if channel not in {"conversation", "workbench", "status", "silent_audit"}:
        channel = "workbench" if event not in {"assistant_delta", "assistant_final"} else "conversation"
    if not visible:
        if channel == "conversation":
            visible = "user_dialogue"
        elif channel == "silent_audit":
            visible = "audit"
        elif event in {"error", "execution_report"}:
            visible = "diagnostic"
        else:
            visible = "progress" if channel == "status" else "task_telemetry"
    if not kind:
        if event in {"tool_started", "tool_progress", "tool_result"}:
            kind = "tool_step"
        elif event == "quality_gate":
            kind = "quality_gate"
        elif event == "audit_event":
            kind = "audit"
        elif event == "approval_required":
            kind = "approval_required"
        elif event == "error":
            kind = "error_summary"
        elif event in {"assistant_final", "run_terminal", "execution_report"}:
            kind = "final"
        else:
            kind = "task_progress"
    return channel, visible, kind


def sanitize_event_payload(value: Any) -> Any:
    """Sanitize one SSE payload before it reaches UI state.

    The frontend may consume public Runtime events only. This is a defensive
    projection layer: credentials, provider endpoints, local paths, and bearer
    tokens are redacted even if a backend event accidentally contains them.
    """
    if isinstance(value, Mapping):
        out: Dict[str, Any] = {}
        for key, raw in value.items():
            safe_key = safe_text(key, 80)
            key_norm = safe_key.lower().replace("-", "_")
            if key_norm in SENSITIVE_KEYS:
                if key_norm in {"base_url", "endpoint", "endpoint_url", "provider_base_url"}:
                    out[f"{safe_key}_digest"] = digest_text(raw, 16) if raw else ""
                    out[f"{safe_key}_configured"] = bool(str(raw or "").strip())
                else:
                    out[f"{safe_key}_configured"] = bool(str(raw or "").strip())
                    out[f"{safe_key}_digest"] = digest_text(raw, 16) if raw else ""
                continue
            out[safe_key] = sanitize_event_payload(raw)
        return out
    if isinstance(value, list):
        return [sanitize_event_payload(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_event_payload(item) for item in value]
    if isinstance(value, str):
        text = safe_text(value, 800)
        for pattern in SECRET_PATTERNS:
            text = pattern.sub("<redacted>", text)
        return text
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return safe_text(value, 300)


def parse_sse_bytes(raw: bytes | str) -> List[RuntimeSseEvent]:
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="replace")
    else:
        text = raw
    return list(parse_sse_lines(text.splitlines()))


def parse_sse_lines(lines: Iterable[str | bytes]) -> Iterator[RuntimeSseEvent]:
    event_name = ""
    data_lines: List[str] = []

    def dispatch() -> Optional[RuntimeSseEvent]:
        nonlocal event_name, data_lines
        if not data_lines:
            event_name = ""
            return None
        raw_data = "\n".join(data_lines).strip()
        event_hint = safe_text(event_name, 64)
        event_name = ""
        data_lines = []
        if not raw_data or raw_data == "[DONE]":
            return None
        try:
            parsed = json.loads(raw_data)
        except json.JSONDecodeError:
            parsed = {"event": event_hint or "assistant_delta", "payload": {"content": raw_data}}
        if isinstance(parsed, Mapping):
            return RuntimeSseEvent.from_mapping(parsed, event_hint=event_hint)
        return RuntimeSseEvent.from_mapping({"event": event_hint or "assistant_delta", "payload": {"content": parsed}}, event_hint=event_hint)

    for raw_line in lines:
        if isinstance(raw_line, bytes):
            line = raw_line.decode("utf-8", errors="replace")
        else:
            line = raw_line
        line = line.rstrip("\r\n")
        if line == "":
            event = dispatch()
            if event is not None:
                yield event
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event_name = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
        elif line.startswith("id:") or line.startswith("retry:"):
            continue
    event = dispatch()
    if event is not None:
        yield event


def validate_terminal_order(events: Iterable[RuntimeSseEvent]) -> bool:
    names = [item.event for item in events]
    if "run_terminal" not in names:
        return True
    if "assistant_final" not in names:
        return False
    return names.index("assistant_final") < names.index("run_terminal")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
