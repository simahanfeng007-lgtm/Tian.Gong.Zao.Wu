from __future__ import annotations

"""L6.62 Trace / Observability display contract.

The observability layer is deliberately read-only. It converts already-public
Runtime SSE / Agent UI events into a compact dashboard projection. It does not
call providers, tools, memory writers, audit writers, rollback executors, or
QualityGate bypass paths.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping
import re

OBSERVABILITY_CONTRACT_VERSION = "tiangong.l6_62.trace_observability.v1"
MAX_TRACE_RECORDS = 240

SENSITIVE_KEY_PARTS = (
    "key",
    "token",
    "secret",
    "password",
    "passwd",
    "authorization",
    "base_url",
    "endpoint",
    "url",
    "path",
)
SENSITIVE_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-.]+"),
    re.compile(r"(?i)sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"([A-Za-z]:\\[^\n\r\t]+)"),
    re.compile(r"(/(?:home|Users|mnt|var|etc)/[^\n\r\t]+)"),
)

CATEGORY_BY_SOURCE_EVENT = {
    "run_started": "run",
    "planner_started": "planner",
    "planner_plan": "planner",
    "runtime_state": "runtime",
    "quality_gate": "quality_gate",
    "tool_started": "tool",
    "tool_result": "tool",
    "audit_event": "audit",
    "rollback_ticket": "rollback",
    "rollback_event": "rollback",
    "assistant_delta": "assistant",
    "assistant_final": "assistant",
    "run_terminal": "terminal",
    "error": "error",
}


def _safe_text(value: Any, max_len: int = 240) -> str:
    text = "" if value is None else str(value)
    for pattern in SENSITIVE_PATTERNS:
        text = pattern.sub("<redacted>", text)
    text = text.replace("\r", " ").replace("\n", " ").strip()
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def _digest(value: Any, length: int = 16) -> str:
    text = "" if value is None else str(value)
    if not text:
        return ""
    return sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:length]


def _redacted_payload_summary(payload: Any, *, max_items: int = 8) -> Dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {"value": _safe_text(payload, 160)} if payload not in (None, "") else {}
    out: Dict[str, Any] = {}
    for raw_key, raw_value in list(payload.items())[:max_items]:
        key = _safe_text(raw_key, 60)
        key_norm = key.lower().replace("-", "_")
        if any(part in key_norm for part in SENSITIVE_KEY_PARTS):
            out[f"{key}_configured"] = bool(str(raw_value or "").strip())
            out[f"{key}_digest"] = _digest(raw_value)
            continue
        if isinstance(raw_value, Mapping):
            out[key] = {"keys": sorted(_safe_text(k, 40) for k in raw_value.keys())[:8]}
        elif isinstance(raw_value, list):
            out[key] = {"list_len": len(raw_value)}
        else:
            out[key] = _safe_text(raw_value, 120)
    return out


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass
class TraceRecord:
    seq: int = 0
    event_type: str = "runtime_state"
    source_event: str = "runtime_state"
    category: str = "runtime"
    phase: str = ""
    status: str = ""
    risk_level: str = ""
    decision: str = ""
    audit_ref: str = ""
    gate_ref: str = ""
    rollback_ref: str = ""
    run_id_digest: str = ""
    task_id_digest: str = ""
    display_hint: str = "status_line"
    latency_ms: int = 0
    duration_ms: int = 0
    terminal: bool = False
    timestamp: str = ""
    message: str = ""
    payload_summary: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "TraceRecord":
        payload = data.get("payload") if isinstance(data.get("payload"), Mapping) else data.get("payload_summary", {})
        source_event = _safe_text(data.get("source_event") or data.get("event") or data.get("source") or data.get("event_type") or "runtime_state", 80)
        event_type = _safe_text(data.get("event_type") or source_event, 80)
        summary = _redacted_payload_summary(payload)
        status = _safe_text(data.get("status") or summary.get("status") or data.get("phase") or "", 80)
        risk_level = _safe_text(data.get("risk_level") or summary.get("risk_level") or "", 16)
        decision = _safe_text(data.get("decision") or summary.get("decision") or "", 64)
        message = _safe_text(data.get("message") or summary.get("message") or summary.get("error_code") or summary.get("content") or "", 220)
        return cls(
            seq=_as_int(data.get("seq"), 0),
            event_type=event_type,
            source_event=source_event,
            category=_safe_text(data.get("category") or CATEGORY_BY_SOURCE_EVENT.get(source_event, "runtime"), 40),
            phase=_safe_text(data.get("phase") or status or source_event, 80),
            status=status,
            risk_level=risk_level,
            decision=decision,
            audit_ref=_safe_text(data.get("audit_ref") or summary.get("audit_id") or summary.get("audit_ref") or "", 80),
            gate_ref=_safe_text(data.get("gate_ref") or summary.get("gate_id") or summary.get("quality_gate_id") or "", 80),
            rollback_ref=_safe_text(data.get("rollback_ref") or summary.get("rollback_ticket") or summary.get("rollback_ref") or "", 80),
            run_id_digest=_safe_text(data.get("run_id_digest") or _digest(data.get("run_id")), 32),
            task_id_digest=_safe_text(data.get("task_id_digest") or _digest(data.get("task_id")), 32),
            display_hint=_safe_text(data.get("display_hint", "status_line"), 80),
            latency_ms=_as_int(data.get("latency_ms") or summary.get("latency_ms"), 0),
            duration_ms=_as_int(data.get("duration_ms") or summary.get("duration_ms"), 0),
            terminal=bool(data.get("terminal", False) or source_event == "run_terminal"),
            timestamp=_safe_text(data.get("timestamp") or datetime.now().isoformat(timespec="seconds"), 80),
            message=message,
            payload_summary=summary,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TraceStats:
    total_events: int = 0
    run_events: int = 0
    planner_events: int = 0
    tool_events: int = 0
    quality_gate_events: int = 0
    audit_events: int = 0
    rollback_events: int = 0
    assistant_events: int = 0
    error_events: int = 0
    terminal_events: int = 0
    pending_confirmations: int = 0
    terminal_order_valid: bool = True
    last_seq: int = 0
    last_category: str = ""
    last_event_type: str = ""
    last_error_summary: str = ""

    @classmethod
    def from_records(cls, records: Iterable[TraceRecord]) -> "TraceStats":
        rows = list(records)
        by_category: Dict[str, int] = {}
        for item in rows:
            by_category[item.category] = by_category.get(item.category, 0) + 1
        names = [item.source_event for item in rows]
        terminal_order_valid = True
        if "run_terminal" in names:
            terminal_order_valid = "assistant_final" in names and names.index("assistant_final") < names.index("run_terminal")
        pending = sum(1 for item in rows if item.category == "quality_gate" and item.decision in {"confirmation_required", "requires_confirmation"})
        errors = [item for item in rows if item.category == "error"]
        last = rows[-1] if rows else TraceRecord()
        return cls(
            total_events=len(rows),
            run_events=by_category.get("run", 0),
            planner_events=by_category.get("planner", 0),
            tool_events=by_category.get("tool", 0),
            quality_gate_events=by_category.get("quality_gate", 0),
            audit_events=by_category.get("audit", 0),
            rollback_events=by_category.get("rollback", 0),
            assistant_events=by_category.get("assistant", 0),
            error_events=by_category.get("error", 0),
            terminal_events=by_category.get("terminal", 0),
            pending_confirmations=pending,
            terminal_order_valid=terminal_order_valid,
            last_seq=max((item.seq for item in rows), default=0),
            last_category=last.category,
            last_event_type=last.event_type,
            last_error_summary=errors[-1].message if errors else "",
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def append_trace_record(records: Iterable[TraceRecord], record: TraceRecord, *, limit: int = MAX_TRACE_RECORDS) -> List[TraceRecord]:
    rows = list(records)
    rows.append(record)
    if limit > 0:
        rows = rows[-limit:]
    return rows


def observability_policy() -> Dict[str, Any]:
    return {
        "contract_version": OBSERVABILITY_CONTRACT_VERSION,
        "render_only": True,
        "no_frontend_tool_execution": True,
        "no_frontend_provider_call": True,
        "no_frontend_memory_write": True,
        "no_frontend_audit_write": True,
        "no_frontend_rollback_apply": True,
        "stores_raw_prompt": False,
        "stores_raw_secret": False,
        "uses_digest_for_run_task_ids": True,
        "max_trace_records": MAX_TRACE_RECORDS,
        "categories": sorted(set(CATEGORY_BY_SOURCE_EVENT.values())),
    }
