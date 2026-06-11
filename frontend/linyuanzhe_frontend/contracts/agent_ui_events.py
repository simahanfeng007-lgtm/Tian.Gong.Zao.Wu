from __future__ import annotations

"""L6.55 Agent UI event contract.

This module normalizes Runtime SSE events into display-only Agent UI events.
It intentionally contains no provider SDK access, no tool execution hooks, no
memory writes, and no rollback/self-iteration apply path. The frontend may use
these events to render transcript deltas, action guard cards, audit badges, and
terminal states only.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Mapping

from .runtime_snapshot import safe_text
from .sse_events import RuntimeSseEvent, sanitize_event_payload


AGENT_UI_CONTRACT_VERSION = "tiangong.l6_55.agent_ui_event.v1"

# Runtime event -> UI event vocabulary. The UI vocabulary is deliberately small:
# enough to make rendering smooth and auditable, not enough to become a command
# surface that could bypass Runtime / QualityGate.
RUNTIME_TO_AGENT_UI_EVENT = {
    "run_started": "run_started",
    "planner_started": "planner_started",
    "planner_plan": "plan_snapshot",
    "runtime_state": "runtime_state",
    "quality_gate": "quality_gate_required",
    "tool_started": "tool_call_started",
    "tool_result": "tool_call_finished",
    "execution_report": "execution_report",
    "audit_event": "audit_recorded",
    "rollback_ticket": "rollback_readonly",
    "rollback_event": "rollback_readonly",
    "assistant_delta": "text_delta",
    "assistant_final": "assistant_final",
    "run_terminal": "run_terminal",
    "error": "error",
}

DISPLAY_HINT_BY_EVENT = {
    "run_started": "status_line",
    "planner_started": "status_line",
    "plan_snapshot": "plan_card_collapsed",
    "runtime_state": "status_line",
    "quality_gate_required": "action_guard_card",
    "tool_call_started": "tool_card_collapsed",
    "tool_call_finished": "tool_card_collapsed",
    "execution_report": "execution_report_card",
    "audit_recorded": "audit_badge",
    "rollback_readonly": "rollback_readonly_card",
    "text_delta": "transcript_delta",
    "assistant_final": "transcript_final",
    "run_terminal": "terminal_marker",
    "error": "error_boundary",
}

FRONTEND_PERMISSION_FLAGS = {
    "render_only": True,
    "no_frontend_tool_execution": True,
    "no_frontend_provider_call": True,
    "no_frontend_memory_write": True,
    "no_frontend_audit_write": True,
    "no_frontend_rollback_apply": True,
    "no_frontend_self_iteration_apply": True,
}


@dataclass(frozen=True)
class AgentUiEvent:
    event_type: str
    run_id: str = ""
    task_id: str = ""
    seq: int = 0
    phase: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    display_hint: str = "status_line"
    display_channel: str = ""
    visibility: str = ""
    event_kind: str = ""
    audit_ref: str = ""
    gate_ref: str = ""
    rollback_ref: str = ""
    terminal: bool = False
    source_event: str = ""
    contract_version: str = AGENT_UI_CONTRACT_VERSION
    permissions: Dict[str, bool] = field(default_factory=lambda: dict(FRONTEND_PERMISSION_FLAGS))

    @classmethod
    def from_runtime_event(cls, event: RuntimeSseEvent) -> "AgentUiEvent":
        payload = event.payload if isinstance(event.payload, Mapping) else {}
        clean_payload = sanitize_event_payload(payload)
        if not isinstance(clean_payload, Mapping):
            clean_payload = {"value": clean_payload}

        event_type = RUNTIME_TO_AGENT_UI_EVENT.get(event.event, "runtime_state")
        display_hint = DISPLAY_HINT_BY_EVENT.get(event_type, "status_line")
        display_channel = safe_text(getattr(event, "display_channel", "") or clean_payload.get("display_channel") or "", 40)
        visibility = safe_text(getattr(event, "visibility", "") or clean_payload.get("visibility") or "", 40)
        event_kind = safe_text(getattr(event, "event_kind", "") or clean_payload.get("event_kind") or "", 40)
        if display_channel in {"workbench", "status", "silent_audit"} and display_hint in {"transcript_delta", "transcript_final"}:
            display_hint = "status_line" if display_channel == "status" else "tool_card_collapsed"
        phase = safe_text(
            clean_payload.get("phase")
            or clean_payload.get("status")
            or clean_payload.get("decision")
            or event.event,
            80,
        )
        audit_ref = safe_text(clean_payload.get("audit_id") or clean_payload.get("audit_ref"), 80)
        gate_ref = safe_text(clean_payload.get("gate_id") or clean_payload.get("quality_gate_id"), 80)
        rollback_ref = safe_text(clean_payload.get("rollback_ticket") or clean_payload.get("rollback_ref"), 80)
        terminal = bool(clean_payload.get("terminal", False) or event.event == "run_terminal")

        return cls(
            event_type=event_type,
            run_id=event.run_id,
            task_id=event.task_id,
            seq=event.seq,
            phase=phase,
            payload=dict(clean_payload),
            display_hint=display_hint,
            display_channel=display_channel,
            visibility=visibility,
            event_kind=event_kind,
            audit_ref=audit_ref,
            gate_ref=gate_ref,
            rollback_ref=rollback_ref,
            terminal=terminal,
            source_event=event.event,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def agent_ui_policy() -> Dict[str, Any]:
    return {
        "contract_version": AGENT_UI_CONTRACT_VERSION,
        "event_vocabulary": sorted(set(RUNTIME_TO_AGENT_UI_EVENT.values())),
        "display_hints": sorted(set(DISPLAY_HINT_BY_EVENT.values())),
        **FRONTEND_PERMISSION_FLAGS,
    }
