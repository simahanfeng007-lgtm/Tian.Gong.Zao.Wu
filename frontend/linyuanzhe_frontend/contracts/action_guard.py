from __future__ import annotations

"""L6.55 QualityGate action-guard and read-only evidence contracts.

The desktop frontend may render these cards and submit a decision request to the
Runtime gateway. It must not execute tools, approve locally, write audit records,
apply rollback, or merge self-iteration candidates.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, List, Mapping

import hashlib
import re


_SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|private[_-]?key)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)(mockkey_[A-Za-z0-9_\-]{8,})"),
    re.compile(r"(?i)(bearer\s+[A-Za-z0-9_\-.]+)"),
]


def safe_text(value: Any, max_len: int = 260) -> str:
    text = "" if value is None else str(value)
    for pattern in _SENSITIVE_PATTERNS:
        text = pattern.sub("<redacted>", text)
    text = text.replace("\r", " ").replace("\n", " ").strip()
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def digest_text(value: Any, length: int = 16) -> str:
    data = ("" if value is None else str(value)).encode("utf-8", errors="ignore")
    return hashlib.sha256(data).hexdigest()[:length]


ACTION_GUARD_CONTRACT_VERSION = "tiangong.l6_55.action_guard_cards.v1"
CONFIRMATION_ENDPOINT = "/confirmations/submit"
ALLOWED_CONFIRMATION_DECISIONS = ("approve", "reject", "request_changes")
DECISION_ALIASES = {
    "confirmed": "approve",
    "confirm": "approve",
    "approved": "approve",
    "allow": "approve",
    "allowed": "approve",
    "rejected": "reject",
    "deny": "reject",
    "denied": "reject",
    "change": "request_changes",
    "edit": "request_changes",
    "modify": "request_changes",
    "request_change": "request_changes",
}


@dataclass(frozen=True)
class ActionGuardCard:
    gate_id: str = ""
    ticket_id: str = ""
    risk_level: str = "A0"
    decision: str = "allowed"
    title: str = "QualityGate 行动守卫"
    action_summary: str = ""
    impact_scope: str = ""
    plan_steps: List[str] = field(default_factory=list)
    allowed_decisions: List[str] = field(default_factory=lambda: list(ALLOWED_CONFIRMATION_DECISIONS))
    audit_ref: str = ""
    rollback_ref: str = ""
    requires_user_confirmation: bool = False
    status: str = "display_only"
    contract_version: str = ACTION_GUARD_CONTRACT_VERSION
    no_frontend_execute: bool = True
    no_frontend_gate_bypass: bool = True
    no_frontend_rollback_apply: bool = True
    no_frontend_audit_write: bool = True

    @classmethod
    def from_quality_gate_payload(cls, payload: Mapping[str, Any]) -> "ActionGuardCard":
        raw_steps = payload.get("plan_steps") or payload.get("steps") or payload.get("affected_steps") or []
        if isinstance(raw_steps, str):
            raw_steps = [raw_steps]
        if not isinstance(raw_steps, Iterable):
            raw_steps = []
        decision = safe_text(payload.get("decision", "allowed"), 64)
        risk = safe_text(payload.get("risk_level", "A0"), 16)
        requires = bool(
            payload.get("requires_user_confirmation")
            or payload.get("human_in_the_loop")
            or decision in {"confirmation_required", "requires_confirmation", "blocked", "A5 blocked"}
            or risk == "A5"
        )
        gate_id = safe_text(payload.get("gate_id") or payload.get("quality_gate_id") or payload.get("id") or "", 80)
        ticket_id = safe_text(
            payload.get("ticket_id")
            or payload.get("confirmation_ticket_id")
            or payload.get("confirmation_id")
            or gate_id,
            80,
        )
        return cls(
            gate_id=gate_id,
            ticket_id=ticket_id,
            risk_level=risk,
            decision=decision,
            title=safe_text(payload.get("title", "QualityGate 行动守卫"), 120),
            action_summary=safe_text(payload.get("action_summary") or payload.get("summary") or payload.get("reason") or "", 240),
            impact_scope=safe_text(payload.get("impact_scope") or payload.get("scope") or "", 240),
            plan_steps=[safe_text(item, 120) for item in list(raw_steps)[:12]],
            audit_ref=safe_text(payload.get("audit_id") or payload.get("audit_ref"), 80),
            rollback_ref=safe_text(payload.get("rollback_ticket") or payload.get("rollback_ref"), 80),
            requires_user_confirmation=requires,
            status="pending_user_confirmation" if requires else "display_only",
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuditReadonlyCard:
    audit_id: str = ""
    event_type: str = "audit_event"
    digest: str = ""
    summary: str = ""
    evidence_ref: str = ""
    count: int = 0
    contract_version: str = ACTION_GUARD_CONTRACT_VERSION
    read_only: bool = True
    no_frontend_audit_write: bool = True

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any], *, count: int = 0) -> "AuditReadonlyCard":
        audit_id = safe_text(payload.get("audit_id") or payload.get("audit_ref") or payload.get("evidence_ref") or "", 80)
        summary = safe_text(payload.get("summary") or payload.get("message") or payload.get("event") or "审计事件已记录", 240)
        return cls(
            audit_id=audit_id,
            event_type=safe_text(payload.get("event_type", "audit_event"), 80),
            digest=safe_text(payload.get("digest") or digest_text(str(payload), 16), 80),
            summary=summary,
            evidence_ref=safe_text(payload.get("evidence_ref") or audit_id, 80),
            count=int(count or 0),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RollbackReadonlyCard:
    rollback_ref: str = ""
    ticket_id: str = ""
    status: str = "available"
    summary: str = ""
    affected_scope: str = ""
    audit_ref: str = ""
    contract_version: str = ACTION_GUARD_CONTRACT_VERSION
    read_only: bool = True
    no_frontend_rollback_apply: bool = True

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "RollbackReadonlyCard":
        ticket = safe_text(payload.get("rollback_ticket") or payload.get("rollback_ref") or payload.get("ticket_id") or "", 80)
        return cls(
            rollback_ref=safe_text(payload.get("rollback_ref") or ticket, 80),
            ticket_id=ticket,
            status=safe_text(payload.get("status") or payload.get("state") or "available", 80),
            summary=safe_text(payload.get("summary") or payload.get("rollback_plan") or payload.get("message") or "回滚票据只读展示", 240),
            affected_scope=safe_text(payload.get("affected_scope") or payload.get("impact_scope") or payload.get("scope") or "", 240),
            audit_ref=safe_text(payload.get("audit_id") or payload.get("audit_ref") or "", 80),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConfirmationRequestEnvelope:
    ticket_id: str
    decision: str
    run_id: str = ""
    task_id: str = ""
    user_comment: str = ""
    frontend_contract: str = ACTION_GUARD_CONTRACT_VERSION
    no_frontend_execute: bool = True
    no_frontend_gate_bypass: bool = True
    no_frontend_audit_write: bool = True
    no_frontend_rollback_apply: bool = True
    route_to_runtime_only: bool = True

    @classmethod
    def build(cls, *, ticket_id: str, decision: str, run_id: str = "", task_id: str = "", user_comment: str = "") -> "ConfirmationRequestEnvelope":
        normalized = normalize_confirmation_decision(decision)
        return cls(
            ticket_id=safe_text(ticket_id, 80),
            decision=normalized,
            run_id=safe_text(run_id, 80),
            task_id=safe_text(task_id, 80),
            user_comment=safe_text(user_comment, 240),
        )

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


def normalize_confirmation_decision(decision: str) -> str:
    text = safe_text(decision, 64).lower()
    text = DECISION_ALIASES.get(text, text)
    if text not in ALLOWED_CONFIRMATION_DECISIONS:
        return "request_changes"
    return text


def action_guard_policy() -> Dict[str, Any]:
    return {
        "contract_version": ACTION_GUARD_CONTRACT_VERSION,
        "confirmation_endpoint": CONFIRMATION_ENDPOINT,
        "allowed_confirmation_decisions": list(ALLOWED_CONFIRMATION_DECISIONS),
        "frontend_permission": "render_and_request_only",
        "no_frontend_execute": True,
        "no_frontend_gate_bypass": True,
        "no_frontend_audit_write": True,
        "no_frontend_rollback_apply": True,
    }
