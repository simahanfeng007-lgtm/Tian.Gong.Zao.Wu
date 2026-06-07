from __future__ import annotations

"""L6.63 deterministic HookBus contract.

The HookBus is a frontend-side policy projection and request guard. It is
intentionally deterministic and local: it does not execute shell commands, call
providers, call tools, write memory, write audit logs, or apply rollback. It
only validates outbound request envelopes and inbound Runtime public events,
then records sanitized hook decisions for the desktop UI.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from hashlib import sha256
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence
import re

HOOK_BUS_CONTRACT_VERSION = "tiangong.l6_65.deterministic_hook_bus.v3"
MAX_HOOK_RECORDS = 180

HOOK_STAGE_PRE_CHAT_SUBMIT = "pre_chat_submit"
HOOK_STAGE_PRE_PROVIDER_SETTINGS_SUBMIT = "pre_provider_settings_submit"
HOOK_STAGE_PRE_CONFIRMATION_SUBMIT = "pre_confirmation_submit"
HOOK_STAGE_PRE_CONTROL_REQUEST = "pre_control_request"
HOOK_STAGE_PRE_SELF_ITERATION_CONFIRM = "pre_self_iteration_confirm"
HOOK_STAGE_PRE_FILE_TRANSFER_REQUEST = "pre_file_transfer_request"
HOOK_STAGE_PRE_WORKSPACE_AUTHORIZATION_REQUEST = "pre_workspace_authorization_request"
HOOK_STAGE_PRE_CONNECTOR_REGISTRATION_REQUEST = "pre_connector_registration_request"
HOOK_STAGE_PRE_EVENT_APPLY = "pre_event_apply"
HOOK_STAGE_POST_EVENT_APPLY = "post_event_apply"
HOOK_STAGE_PRE_FINALIZE = "pre_finalize"
HOOK_STAGE_ON_ERROR = "on_error"

HOOK_STAGES = (
    HOOK_STAGE_PRE_CHAT_SUBMIT,
    HOOK_STAGE_PRE_PROVIDER_SETTINGS_SUBMIT,
    HOOK_STAGE_PRE_CONFIRMATION_SUBMIT,
    HOOK_STAGE_PRE_CONTROL_REQUEST,
    HOOK_STAGE_PRE_SELF_ITERATION_CONFIRM,
    HOOK_STAGE_PRE_FILE_TRANSFER_REQUEST,
    HOOK_STAGE_PRE_WORKSPACE_AUTHORIZATION_REQUEST,
    HOOK_STAGE_PRE_CONNECTOR_REGISTRATION_REQUEST,
    HOOK_STAGE_PRE_EVENT_APPLY,
    HOOK_STAGE_POST_EVENT_APPLY,
    HOOK_STAGE_PRE_FINALIZE,
    HOOK_STAGE_ON_ERROR,
)

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
    "run_id",
    "task_id",
)
SENSITIVE_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-.]+"),
    re.compile(r"(?i)sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"([A-Za-z]:\\[^\n\r\t]+)"),
    re.compile(r"(/(?:home|Users|mnt|var|etc)/[^\n\r\t]+)"),
)

ALLOW_DECISIONS = {"allowed", "allow", "pass", "ok", "approved"}
CONFIRMATION_DECISIONS = {"confirmation_required", "requires_confirmation", "manual_review", "pending_user_confirmation"}
BLOCK_DECISIONS = {"blocked", "block", "deny", "denied", "rejected", "a5 blocked", "blocked_by_hook"}
VALID_CONFIRMATION_DECISIONS = {"approve", "reject", "request_changes", "confirmed", "rejected", "allow", "deny"}
VALID_CONTROL_ACTIONS = {"stop", "reset", "interrupt", "resume", "search"}
VALID_WORKSPACE_AUTH_MODES = {"read", "write", "read_write", "download"}
VALID_WORKSPACE_SCOPES = {"user_selected_file", "workspace_inbox", "workspace_outbox", "artifact_download", "temporary_handoff"}
VALID_CONNECTOR_KINDS = {"mcp_server", "local_connector", "remote_connector", "document_connector", "browser_connector", "workflow_connector"}
VALID_CONNECTOR_MODES = {"disabled", "read_only", "request_only", "quarantined"}


def _safe_text(value: Any, max_len: int = 220) -> str:
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


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _payload_summary(payload: Any, *, max_items: int = 10) -> Dict[str, Any]:
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


def _event_payload(context: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = context.get("payload", {})
    return payload if isinstance(payload, Mapping) else {}


@dataclass(frozen=True)
class HookDecision:
    ok: bool = True
    verdict: str = "allow"
    severity: str = "info"
    rule_id: str = "default_allow"
    reason: str = "allowed"
    require_runtime_route: bool = True
    frontend_may_execute: bool = False
    frontend_may_write_memory: bool = False
    frontend_may_write_audit: bool = False
    frontend_may_apply_rollback: bool = False
    requires_user_confirmation: bool = False

    @classmethod
    def allow(cls, rule_id: str, reason: str = "allowed", *, severity: str = "info") -> "HookDecision":
        return cls(ok=True, verdict="allow", severity=severity, rule_id=rule_id, reason=_safe_text(reason, 180))

    @classmethod
    def warn(cls, rule_id: str, reason: str) -> "HookDecision":
        return cls(ok=True, verdict="warn", severity="warning", rule_id=rule_id, reason=_safe_text(reason, 180))

    @classmethod
    def block(cls, rule_id: str, reason: str, *, requires_user_confirmation: bool = False) -> "HookDecision":
        return cls(
            ok=False,
            verdict="block",
            severity="error",
            rule_id=rule_id,
            reason=_safe_text(reason, 180),
            requires_user_confirmation=requires_user_confirmation,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HookRule:
    rule_id: str
    stage: str
    description: str
    fn: Callable[[Mapping[str, Any]], HookDecision]
    enabled: bool = True


@dataclass
class HookRecord:
    seq: int = 0
    stage: str = "pre_event_apply"
    rule_id: str = "default_allow"
    verdict: str = "allow"
    severity: str = "info"
    reason: str = "allowed"
    source_event: str = ""
    run_id_digest: str = ""
    task_id_digest: str = ""
    ticket_id_digest: str = ""
    payload_summary: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    @classmethod
    def from_decision(cls, *, seq: int, stage: str, decision: HookDecision, context: Mapping[str, Any]) -> "HookRecord":
        payload = context.get("payload", context)
        if not isinstance(payload, Mapping):
            payload = {}
        ticket_id = context.get("ticket_id") or payload.get("ticket_id") or payload.get("gate_id") or ""
        return cls(
            seq=seq,
            stage=_safe_text(stage, 80),
            rule_id=_safe_text(decision.rule_id, 100),
            verdict=_safe_text(decision.verdict, 40),
            severity=_safe_text(decision.severity, 40),
            reason=_safe_text(decision.reason, 220),
            source_event=_safe_text(context.get("event") or context.get("source_event") or payload.get("event") or "", 80),
            run_id_digest=_digest(context.get("run_id") or payload.get("run_id")),
            task_id_digest=_digest(context.get("task_id") or payload.get("task_id")),
            ticket_id_digest=_digest(ticket_id),
            payload_summary=_payload_summary(payload),
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "HookRecord":
        summary = data.get("payload_summary", {}) if isinstance(data.get("payload_summary"), Mapping) else {}
        return cls(
            seq=int(data.get("seq", 0) or 0),
            stage=_safe_text(data.get("stage", "pre_event_apply"), 80),
            rule_id=_safe_text(data.get("rule_id", "default_allow"), 100),
            verdict=_safe_text(data.get("verdict", "allow"), 40),
            severity=_safe_text(data.get("severity", "info"), 40),
            reason=_safe_text(data.get("reason", "allowed"), 220),
            source_event=_safe_text(data.get("source_event", ""), 80),
            run_id_digest=_safe_text(data.get("run_id_digest", ""), 32),
            task_id_digest=_safe_text(data.get("task_id_digest", ""), 32),
            ticket_id_digest=_safe_text(data.get("ticket_id_digest", ""), 32),
            payload_summary=dict(summary),
            timestamp=_safe_text(data.get("timestamp", ""), 80),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HookStats:
    total_hooks: int = 0
    allow_count: int = 0
    warn_count: int = 0
    block_count: int = 0
    last_stage: str = ""
    last_rule_id: str = ""
    last_verdict: str = ""
    last_blocker: str = ""
    deterministic: bool = True
    frontend_execute_allowed: bool = False
    frontend_memory_write_allowed: bool = False
    frontend_audit_write_allowed: bool = False
    frontend_rollback_apply_allowed: bool = False

    @classmethod
    def from_records(cls, records: Iterable[HookRecord]) -> "HookStats":
        rows = list(records)
        allow = sum(1 for item in rows if item.verdict == "allow")
        warn = sum(1 for item in rows if item.verdict == "warn")
        block = sum(1 for item in rows if item.verdict == "block")
        last = rows[-1] if rows else HookRecord()
        blockers = [item for item in rows if item.verdict == "block"]
        return cls(
            total_hooks=len(rows),
            allow_count=allow,
            warn_count=warn,
            block_count=block,
            last_stage=last.stage,
            last_rule_id=last.rule_id,
            last_verdict=last.verdict,
            last_blocker=blockers[-1].reason if blockers else "",
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _rule_required_runtime_flags(context: Mapping[str, Any]) -> HookDecision:
    payload = context.get("payload", context)
    if not isinstance(payload, Mapping):
        return HookDecision.block("required_runtime_flags", "payload must be mapping")
    required = {
        "no_frontend_tool_execution": True,
        "no_frontend_memory_write": True,
        "no_frontend_rollback_apply": True,
    }
    missing = [key for key, expected in required.items() if payload.get(key) is not expected]
    if missing:
        return HookDecision.block("required_runtime_flags", "missing or false frontend safety flags: " + ", ".join(missing))
    return HookDecision.allow("required_runtime_flags", "chat payload routes to Runtime and disables frontend execution")


def _rule_provider_write_only(context: Mapping[str, Any]) -> HookDecision:
    payload = context.get("payload", context)
    if not isinstance(payload, Mapping):
        return HookDecision.block("provider_write_only", "provider settings payload must be mapping")
    if not payload.get("frontend_contract"):
        return HookDecision.block("provider_write_only", "provider write request missing frontend_contract")
    raw_key_present = bool(str(payload.get("api_key", "")).strip())
    raw_base_present = bool(str(payload.get("base_url", "")).strip())
    if not raw_key_present and not raw_base_present:
        return HookDecision.warn("provider_write_only", "provider write request contains no credential fields; read-only refresh may be intended")
    return HookDecision.allow("provider_write_only", "raw credential fields are outbound-only to Runtime; HookRecord stores configured/digest only")


def _rule_confirmation_ticket_required(context: Mapping[str, Any]) -> HookDecision:
    payload = context.get("payload", context)
    if not isinstance(payload, Mapping):
        return HookDecision.block("confirmation_ticket_required", "confirmation payload must be mapping")
    ticket_id = str(payload.get("ticket_id", "")).strip()
    decision = str(payload.get("decision", "")).strip().lower()
    if not ticket_id:
        return HookDecision.block("confirmation_ticket_required", "confirmation request missing ticket_id", requires_user_confirmation=True)
    if decision not in VALID_CONFIRMATION_DECISIONS:
        return HookDecision.block("confirmation_ticket_required", "confirmation decision is not in allowed vocabulary", requires_user_confirmation=True)
    if payload.get("frontend_contract") is None:
        return HookDecision.warn("confirmation_ticket_required", "confirmation request has ticket_id but no frontend_contract marker")
    return HookDecision.allow("confirmation_ticket_required", "confirmation is request-only and routed to Runtime")


def _rule_control_request_request_only(context: Mapping[str, Any]) -> HookDecision:
    payload = context.get("payload", context)
    if not isinstance(payload, Mapping):
        return HookDecision.block("control_request_only", "control request payload must be mapping")
    action = str(payload.get("action", "")).strip().lower()
    if action not in VALID_CONTROL_ACTIONS:
        return HookDecision.block("control_request_only", "control action must be stop, reset, interrupt, resume, or search")
    if payload.get("no_frontend_execute") is not True and payload.get("no_frontend_tool_execution") is not True:
        return HookDecision.block("control_request_only", "control request missing no_frontend_execute/no_frontend_tool_execution")
    if payload.get("no_frontend_memory_write") is not True or payload.get("no_frontend_rollback_apply") is not True:
        return HookDecision.block("control_request_only", "control request missing memory/rollback safety flags")
    return HookDecision.allow("control_request_only", "stop/reset/interrupt/resume/search are Runtime requests only")


def _rule_self_iteration_request_only(context: Mapping[str, Any]) -> HookDecision:
    payload = context.get("payload", context)
    if not isinstance(payload, Mapping):
        return HookDecision.block("self_iteration_request_only", "self-iteration payload must be mapping")
    if not str(payload.get("candidate_id", "")).strip():
        return HookDecision.block("self_iteration_request_only", "self-iteration confirmation missing candidate_id")
    if payload.get("no_frontend_self_iteration_apply") is not True:
        return HookDecision.block("self_iteration_request_only", "self-iteration request missing no_frontend_self_iteration_apply")
    return HookDecision.allow("self_iteration_request_only", "self-iteration confirmation is request-only")


def _rule_file_transfer_request_only(context: Mapping[str, Any]) -> HookDecision:
    payload = context.get("payload", context)
    if not isinstance(payload, Mapping):
        return HookDecision.block("file_transfer_request_only", "file transfer payload must be mapping")
    if payload.get("route_to_runtime_only") is not True:
        return HookDecision.block("file_transfer_request_only", "file transfer must route to Runtime only")
    required = ("no_frontend_tool_execution", "no_frontend_memory_write", "no_frontend_audit_write", "no_frontend_rollback_apply", "no_frontend_path_exposure")
    missing = [key for key in required if payload.get(key) is not True]
    if missing:
        return HookDecision.block("file_transfer_request_only", "file transfer missing safety flags: " + ", ".join(missing))
    if payload.get("raw_content_inline") is not False:
        return HookDecision.block("file_transfer_request_only", "file transfer may not inline raw content in RC request envelope")
    if not str(payload.get("file_name", "")).strip():
        return HookDecision.block("file_transfer_request_only", "file transfer missing file_name")
    if int(payload.get("size_bytes", 0) or 0) <= 0:
        return HookDecision.block("file_transfer_request_only", "file transfer size must be positive")
    if len(str(payload.get("sha256", "")).strip()) < 32:
        return HookDecision.block("file_transfer_request_only", "file transfer missing sha256 digest")
    return HookDecision.allow("file_transfer_request_only", "file transfer is a sanitized Runtime handoff request")

def _rule_workspace_authorization_request_only(context: Mapping[str, Any]) -> HookDecision:
    payload = context.get("payload", context)
    if not isinstance(payload, Mapping):
        return HookDecision.block("workspace_authorization_request_only", "workspace authorization payload must be mapping")
    if payload.get("route_to_runtime_only") is not True:
        return HookDecision.block("workspace_authorization_request_only", "workspace authorization must route to Runtime only")
    required = (
        "no_frontend_workspace_create",
        "no_frontend_acl_mutation",
        "no_frontend_file_copy",
        "no_frontend_memory_write",
        "no_frontend_audit_write",
        "no_frontend_rollback_apply",
        "no_frontend_path_exposure",
    )
    missing = [key for key in required if payload.get(key) is not True]
    if missing:
        return HookDecision.block("workspace_authorization_request_only", "workspace authorization missing safety flags: " + ", ".join(missing))
    if payload.get("raw_content_inline") is not False:
        return HookDecision.block("workspace_authorization_request_only", "workspace authorization may not inline raw file content")
    mode = str(payload.get("mode", "")).strip().lower()
    scope = str(payload.get("scope", "")).strip()
    if mode not in VALID_WORKSPACE_AUTH_MODES:
        return HookDecision.block("workspace_authorization_request_only", "workspace authorization mode is not allowed")
    if scope not in VALID_WORKSPACE_SCOPES:
        return HookDecision.block("workspace_authorization_request_only", "workspace authorization scope is not allowed")
    if not str(payload.get("file_name", "")).strip():
        return HookDecision.block("workspace_authorization_request_only", "workspace authorization missing file_name")
    if mode in {"write", "read_write"}:
        return HookDecision.warn("workspace_authorization_request_only", "write-capable workspace authorization must remain Runtime/QualityGate governed")
    return HookDecision.allow("workspace_authorization_request_only", "workspace authorization is a sanitized Runtime request")



def _rule_connector_registration_request_only(context: Mapping[str, Any]) -> HookDecision:
    payload = context.get("payload", context)
    if not isinstance(payload, Mapping):
        return HookDecision.block("connector_registration_request_only", "connector registration payload must be mapping")
    if payload.get("route_to_runtime_only") is not True:
        return HookDecision.block("connector_registration_request_only", "connector registration must route to Runtime only")
    required = (
        "no_frontend_connector_install",
        "no_frontend_connector_execute",
        "no_frontend_secret_storage",
        "no_frontend_workspace_bypass",
        "no_frontend_tool_execution",
        "no_frontend_memory_write",
        "no_frontend_audit_write",
        "no_frontend_rollback_apply",
        "no_raw_endpoint_display",
        "no_mcp_market_install",
    )
    missing = [key for key in required if payload.get(key) is not True]
    if missing:
        return HookDecision.block("connector_registration_request_only", "connector registration missing safety flags: " + ", ".join(missing))
    if payload.get("raw_manifest_inline") is not False:
        return HookDecision.block("connector_registration_request_only", "connector registration may not inline raw manifest in RC request envelope")
    kind = str(payload.get("kind", "")).strip()
    mode = str(payload.get("default_mode", "")).strip()
    if kind not in VALID_CONNECTOR_KINDS:
        return HookDecision.block("connector_registration_request_only", "connector kind is not allowed")
    if mode not in VALID_CONNECTOR_MODES:
        return HookDecision.block("connector_registration_request_only", "connector default_mode is not allowed")
    if mode not in {"disabled", "read_only", "request_only", "quarantined"}:
        return HookDecision.block("connector_registration_request_only", "connector may not default to executable mode")
    if not str(payload.get("display_name", "")).strip():
        return HookDecision.block("connector_registration_request_only", "connector registration missing display_name")
    if len(str(payload.get("manifest_digest", "")).strip()) < 8:
        return HookDecision.block("connector_registration_request_only", "connector registration missing manifest digest")
    return HookDecision.allow("connector_registration_request_only", "connector registration is a sanitized Runtime request")


def _rule_a5_cannot_be_allowed(context: Mapping[str, Any]) -> HookDecision:
    event = str(context.get("event") or context.get("source_event") or "")
    payload = _event_payload(context)
    if event != "quality_gate":
        return HookDecision.allow("a5_cannot_be_allowed", "not a quality_gate event")
    risk = str(payload.get("risk_level", "")).strip().upper()
    decision = str(payload.get("decision", "")).strip()
    decision_norm = decision.lower()
    if risk == "A5" and decision_norm in ALLOW_DECISIONS:
        return HookDecision.block("a5_cannot_be_allowed", "A5 must be blocked or require human confirmation", requires_user_confirmation=True)
    if risk == "A5" and decision_norm not in BLOCK_DECISIONS and decision_norm not in CONFIRMATION_DECISIONS:
        return HookDecision.block("a5_cannot_be_allowed", "A5 decision vocabulary is invalid", requires_user_confirmation=True)
    return HookDecision.allow("a5_cannot_be_allowed", "A5 policy satisfied or not applicable")


def _rule_terminal_order(context: Mapping[str, Any]) -> HookDecision:
    event = str(context.get("event") or context.get("source_event") or "")
    if event != "run_terminal":
        return HookDecision.allow("terminal_order", "not terminal event")
    if not _boolish(context.get("seen_assistant_final")):
        return HookDecision.block("terminal_order", "run_terminal arrived before assistant_final")
    return HookDecision.allow("terminal_order", "assistant_final observed before run_terminal")


def _rule_event_payload_redaction(context: Mapping[str, Any]) -> HookDecision:
    payload = context.get("payload", {})
    text = str(payload)
    redacted = _safe_text(text, max_len=1000)
    if "<redacted>" in redacted:
        return HookDecision.warn("event_payload_redaction", "payload contains sensitive-looking material; display projection must stay redacted")
    return HookDecision.allow("event_payload_redaction", "payload projection is display-safe")


def _rule_finalize_trace(context: Mapping[str, Any]) -> HookDecision:
    if not _boolish(context.get("terminal_order_valid", True)):
        return HookDecision.block("finalize_trace", "terminal order invalid at finalize")
    return HookDecision.allow("finalize_trace", "finalize checks passed")


def _rule_error_recorded(context: Mapping[str, Any]) -> HookDecision:
    if context.get("error"):
        return HookDecision.warn("error_recorded", "frontend captured error and converted it to sanitized projection")
    return HookDecision.allow("error_recorded", "no error")


class HookBus:
    """Deterministic, in-process rule runner for frontend request/event guards."""

    def __init__(self, rules: Sequence[HookRule]) -> None:
        self.rules = tuple(rule for rule in rules if rule.enabled)
        self.records: List[HookRecord] = []
        self._seq = 0

    @classmethod
    def default_frontend_bus(cls) -> "HookBus":
        return cls(
            (
                HookRule("required_runtime_flags", HOOK_STAGE_PRE_CHAT_SUBMIT, "chat payload must route to Runtime and disable frontend execution", _rule_required_runtime_flags),
                HookRule("provider_write_only", HOOK_STAGE_PRE_PROVIDER_SETTINGS_SUBMIT, "provider credentials are outbound-only; reports keep digest/configured flags", _rule_provider_write_only),
                HookRule("confirmation_ticket_required", HOOK_STAGE_PRE_CONFIRMATION_SUBMIT, "confirmation requests require ticket_id and allowed decision vocabulary", _rule_confirmation_ticket_required),
                HookRule("control_request_only", HOOK_STAGE_PRE_CONTROL_REQUEST, "stop/reset/interrupt/resume/search are Runtime request envelopes only", _rule_control_request_request_only),
                HookRule("self_iteration_request_only", HOOK_STAGE_PRE_SELF_ITERATION_CONFIRM, "self-iteration confirmation never applies locally", _rule_self_iteration_request_only),
                HookRule("file_transfer_request_only", HOOK_STAGE_PRE_FILE_TRANSFER_REQUEST, "file transfer is a sanitized Runtime request only", _rule_file_transfer_request_only),
                HookRule("workspace_authorization_request_only", HOOK_STAGE_PRE_WORKSPACE_AUTHORIZATION_REQUEST, "workspace authorization is a Runtime request envelope only", _rule_workspace_authorization_request_only),
                HookRule("connector_registration_request_only", HOOK_STAGE_PRE_CONNECTOR_REGISTRATION_REQUEST, "connector registration is a Runtime-governed registry request only", _rule_connector_registration_request_only),
                HookRule("a5_cannot_be_allowed", HOOK_STAGE_PRE_EVENT_APPLY, "A5 must be blocked or require confirmation", _rule_a5_cannot_be_allowed),
                HookRule("terminal_order", HOOK_STAGE_PRE_EVENT_APPLY, "run_terminal must follow assistant_final", _rule_terminal_order),
                HookRule("event_payload_redaction", HOOK_STAGE_POST_EVENT_APPLY, "event display projection must stay redacted", _rule_event_payload_redaction),
                HookRule("finalize_trace", HOOK_STAGE_PRE_FINALIZE, "final output closeout checks", _rule_finalize_trace),
                HookRule("error_recorded", HOOK_STAGE_ON_ERROR, "frontend errors are rendered as sanitized state", _rule_error_recorded),
            )
        )

    def evaluate(self, stage: str, context: Optional[Mapping[str, Any]] = None) -> HookDecision:
        safe_stage = _safe_text(stage, 80)
        payload = dict(context or {})
        decisions: List[HookDecision] = []
        for rule in self.rules:
            if rule.stage != safe_stage:
                continue
            try:
                decision = rule.fn(payload)
            except Exception as exc:  # deterministic closed failure
                decision = HookDecision.block(rule.rule_id, f"hook rule exception: {_safe_text(exc, 120)}")
            decisions.append(decision)
            self._append_record(safe_stage, decision, payload)
            if not decision.ok:
                return decision
        if not decisions:
            decision = HookDecision.allow("no_rule_registered", "no hook rule registered for stage")
            self._append_record(safe_stage, decision, payload)
            return decision
        warnings = [item for item in decisions if item.verdict == "warn"]
        if warnings:
            return warnings[-1]
        return decisions[-1]

    def _append_record(self, stage: str, decision: HookDecision, context: Mapping[str, Any]) -> None:
        self._seq += 1
        self.records.append(HookRecord.from_decision(seq=self._seq, stage=stage, decision=decision, context=context))
        self.records = self.records[-MAX_HOOK_RECORDS:]

    def stats(self) -> HookStats:
        return HookStats.from_records(self.records)

    def export_digest(self, length: int = 16) -> str:
        data = [record.to_dict() for record in self.records]
        return sha256(str(data).encode("utf-8", errors="ignore")).hexdigest()[:length]


def hook_bus_policy() -> Dict[str, Any]:
    return {
        "contract_version": HOOK_BUS_CONTRACT_VERSION,
        "deterministic": True,
        "local_only": True,
        "no_shell_execution": True,
        "no_provider_call": True,
        "no_tool_execution": True,
        "no_memory_write": True,
        "no_audit_write": True,
        "no_rollback_apply": True,
        "request_envelope_guard": True,
        "file_transfer_request_guard": True,
        "workspace_authorization_request_guard": True,
        "connector_registration_request_guard": True,
        "event_projection_guard": True,
        "a5_must_block_or_confirm": True,
        "terminal_order_required": True,
        "max_hook_records": MAX_HOOK_RECORDS,
        "stages": list(HOOK_STAGES),
    }
