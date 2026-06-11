"""L6.51 前后端契约冻结。\n\n该模块只导出前端可消费的只读 contract/schema，不执行工具、不读取密钥、\n不写长期记忆、不调用 Provider。前端桌面端必须以这些字段为稳定接入边界。\n"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from tiangong_agent_shell.safe_logging import redact_endpoint, redact_secret, redact_text, sanitize_mapping

from .runtime_report import runtime_result_to_public_dict
from .product_identity import PRODUCT_IDENTITY_ENDPOINT, build_product_identity_public

CONTRACT_VERSION = "tiangong.l6_51_1.frontend_backend_contract.v1"
CHAT_STREAM_ENDPOINT = "/chat/stream-events"
SETTINGS_ENDPOINT = "/settings/provider"
HEALTH_ENDPOINT = "/health/runtime"
METADATA_ENDPOINT = PRODUCT_IDENTITY_ENDPOINT

SSE_EVENT_TYPES = (
    "run_started",
    "planner_started",
    "planner_plan",
    "runtime_state",
    "quality_gate",
    "approval_required",
    "tool_started",
    "tool_progress",
    "tool_result",
    "execution_report",
    "audit_event",
    "assistant_delta",
    "assistant_final",
    "run_terminal",
    "error",
)

TERMINAL_EVENT_ORDER = ("assistant_final", "run_terminal")

DISPLAY_CHANNELS = ("conversation", "workbench", "status", "silent_audit")
VISIBILITY_TYPES = ("user_dialogue", "task_telemetry", "progress", "artifact", "diagnostic", "audit")
EVENT_KIND_TYPES = (
    "assistant_message",
    "user_message",
    "task_progress",
    "tool_step",
    "quality_gate",
    "artifact_ready",
    "error_summary",
    "approval_required",
    "final",
    "audit",
)

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

PROVIDER_SETTING_FIELDS = (
    "provider",
    "model",
    "base_url_digest",
    "api_key_configured",
    "timeout",
    "stream",
    "planner_mode",
    "tool_execution_mode",
)

FRONTEND_FORBIDDEN_ACTIONS = (
    "direct_provider_sdk_call",
    "direct_tool_adapter_call",
    "direct_plan_execution",
    "direct_long_term_memory_write",
    "direct_audit_write",
    "direct_rollback_apply",
    "direct_self_iteration_merge",
    "plaintext_api_key_return",
    "plaintext_base_url_return",
)

ERROR_CODES = (
    "planner_failed",
    "plan_schema_invalid",
    "quality_gate_blocked",
    "confirmation_required",
    "provider_timeout",
    "provider_auth_failed",
    "provider_rate_limited",
    "provider_unavailable",
    "context_overflow",
    "model_policy_blocked",
    "weak_model_not_allowed",
    "runtime_error",
)


@dataclass(frozen=True)
class FrontendContractCheck:
    ok: bool
    contract_version: str = CONTRACT_VERSION
    issues: tuple[str, ...] = ()

    def public_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "contract_version": self.contract_version, "issues": list(self.issues)}


def build_runtime_sse_event_schema() -> dict[str, Any]:
    """返回冻结的 SSE 事件 schema。"""
    base = {
        "event": "<event_type>",
        "seq": "monotonic integer, starts at 1 per run",
        "run_id": "stable runtime run id",
        "task_id": "stable frontend task id or runtime task id",
        "timestamp": "unix seconds or ISO timestamp supplied by gateway",
        "display_channel": "conversation|workbench|status|silent_audit",
        "visibility": "user_dialogue|task_telemetry|progress|artifact|diagnostic|audit",
        "event_kind": "assistant_message|user_message|task_progress|tool_step|quality_gate|artifact_ready|error_summary|approval_required|final|audit",
        "payload": {},
    }
    return {
        "schema": CONTRACT_VERSION,
        "endpoint": CHAT_STREAM_ENDPOINT,
        "transport": "sse",
        "required_envelope_fields": list(base.keys()),
        "event_types": list(SSE_EVENT_TYPES),
        "terminal_order": list(TERMINAL_EVENT_ORDER),
        "events": {
            "run_started": {**base, "payload": {"runtime_status": "active", "provider_model": "safe public model id"}},
            "planner_started": {**base, "payload": {"planner_mode": "rule_only|model_suggest", "schema_required": True}},
            "planner_plan": {**base, "payload": {"steps": "public plan steps", "normalized_by_plan_schema": True}},
            "runtime_state": {**base, "payload": {"phase": "planner|runtime|quality_gate|audit|final", "status_bar": "see status_bar_fields_contract"}},
            "quality_gate": {**base, "payload": {"risk_level": "A0-A5", "decision": "allowed|blocked|confirmation_required", "a5_hard_boundary": True}},
            "tool_started": {**base, "payload": {"step_id": "safe step id", "tool_name": "registered runtime tool"}},
            "tool_result": {**base, "payload": {"step_id": "safe step id", "status": "ok|failed|blocked|skipped|timeout", "audit_ref": "audit id"}},
            "audit_event": {**base, "payload": {"audit_id": "audit id", "digest_only": True}},
            "assistant_delta": {**base, "payload": {"content": "optional incremental safe text"}},
            "assistant_final": {**base, "payload": {"content": "final safe assistant text", "status": "ok|partial_or_failed|planner_failed"}},
            "run_terminal": {**base, "payload": {"terminal": True, "final_event_seen": True, "rollback_ref": "optional ticket/ref"}},
            "error": {**base, "payload": {"error_code": "see error_codes", "message": "redacted user-safe message", "recoverable": True}},
        },
        "security": {
            "no_plain_api_key": True,
            "no_plain_base_url": True,
            "frontend_must_not_execute_tools": True,
            "frontend_must_not_call_provider": True,
            "frontend_must_not_write_memory": True,
        },
    }


def build_provider_settings_contract() -> dict[str, Any]:
    """Provider 设置页契约。API Key 仍为写入型密钥；Base URL 可通过 base_url_display 在设置页显示。"""
    return {
        "schema": CONTRACT_VERSION,
        "endpoint": SETTINGS_ENDPOINT,
        "read_fields": list(PROVIDER_SETTING_FIELDS),
        "write_only_fields": ["api_key"],
        "forbidden_response_fields": ["api_key", "base_url", "authorization", "bearer", "token", "secret", "endpoint"],
        "base_url_display_field": "base_url_display",
        "storage_boundary": "gateway_or_controlled_config_layer_only",
        "frontend_storage": {"api_key_local_storage_plaintext": False, "base_url_ui_preferences_plaintext": True, "logs_plaintext": False},
        "deepseek_alias_env": ["DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL"],
        "canonical_env": ["TIANGONG_API_KEY", "TIANGONG_BASE_URL", "TIANGONG_MODEL"],
        "model_routing_hint": {
            "deepseek-v4-flash": "fast_readonly_or_small_tasks",
            "deepseek-v4-pro": "planner_or_complex_tasks",
        },
    }


def provider_config_to_public_settings(model_config: Any) -> dict[str, Any]:
    """把 ModelConfig 投影成前端安全设置状态。"""
    provider = str(getattr(model_config, "provider", "") or "")
    model = str(getattr(model_config, "model", "") or "")
    base_url = str(getattr(model_config, "base_url", "") or "")
    api_key = str(getattr(model_config, "api_key", "") or "")
    payload = {
        "provider": provider,
        "model": model,
        "base_url_digest": redact_endpoint(base_url),
        "api_key_configured": bool(api_key) and redact_secret(api_key) not in {"<未配置>", "<示例占位>"},
        "timeout": float(getattr(model_config, "timeout", 60.0) or 60.0),
        "stream": bool(getattr(model_config, "stream", False)),
        "planner_mode": getattr(getattr(model_config, "planner_mode", ""), "value", getattr(model_config, "planner_mode", "")),
        "tool_execution_mode": getattr(getattr(model_config, "tool_execution_mode", ""), "value", getattr(model_config, "tool_execution_mode", "")),
    }
    return sanitize_mapping(payload)


def build_status_bar_fields_contract() -> dict[str, Any]:
    return {
        "schema": CONTRACT_VERSION,
        "fields": {
            "runtime_status": "idle|active|planner_failed|partial_or_failed|ok|error",
            "provider_model": "safe provider/model label, no endpoint/key",
            "budget_pool": "main|auxiliary|diagnostic|child_agent|long_chain|extreme|unknown",
            "budget_used_ratio": "0.0-1.0 or not_reported",
            "gate_status": "A0-A4 allowed/confirmation or A5 blocked",
            "audit_id": "latest audit id or digest ref",
            "memory_mode": "readonly|writable_by_runtime|disabled; frontend never writes directly",
            "tools_allowed": "integer count of runtime-registered allowed tools",
            "latency_ms": "integer latency from gateway/runtime measurement",
        },
        "required_fields": list(STATUS_BAR_FIELDS),
        "minimal_home_rule": {
            "fixed_chat_input_required": True,
            "home_should_stay_minimal": True,
            "no_monitor_wall_by_default": True,
        },
    }


def build_frontend_backend_contract() -> dict[str, Any]:
    return {
        "schema": CONTRACT_VERSION,
        "canonical_entry": "TiangongWangguan",
        "runtime_entry": "RuntimeEntry",
        "official_chain": "Planner -> ExecutionSpine -> Runtime -> QualityGate -> Audit/Rollback",
        "chat_stream_endpoint": CHAT_STREAM_ENDPOINT,
        "provider_settings_endpoint": SETTINGS_ENDPOINT,
        "health_endpoint": HEALTH_ENDPOINT,
        "product_metadata_endpoint": METADATA_ENDPOINT,
        "product_identity": build_product_identity_public(),
        "sse_schema": build_runtime_sse_event_schema(),
        "provider_settings": build_provider_settings_contract(),
        "status_bar": build_status_bar_fields_contract(),
        "forbidden_frontend_actions": list(FRONTEND_FORBIDDEN_ACTIONS),
        "error_codes": list(ERROR_CODES),
        "l6_51_1_product_identity_freeze": {
            "unique_developer": "于泳翔",
            "angel_investor": "胖胖龙",
            "runtime_semantics": "metadata_only",
            "frontend_permission": "read_only_display",
        },
        "l6_50_online_smoke_freeze": {
            "mock_smoke": "7/7 pass",
            "real_online_smoke": "4/4 pass",
            "deepseek_v4_pro_basic_chat": "2.3s pass",
            "deepseek_v4_pro_plan_generation": "5.0s pass",
            "deepseek_v4_flash": "0.8s pass",
            "credential_redaction": "no leak",
            "runbook": "PROVIDER_SMOKE_RUNBOOK.md",
            "ci_allowlist_tools": 5,
        },
    }


def runtime_result_to_sse_events(result: Any, *, run_id: str = "", task_id: str = "runtime_text") -> list[dict[str, Any]]:
    """将 RuntimeRunResult 投影为冻结 SSE 顺序样本。

    L6.72.54：所有事件必须带 display_channel / visibility / event_kind。
    会话区只消费 conversation；planner/tool/quality/task report 全部进入 workbench/status/silent_audit。
    """
    public = runtime_result_to_public_dict(result)
    rid = run_id or _stable_ref(public, prefix="run")
    task = str(public.get("task_id") or task_id or "runtime_text")
    events: list[dict[str, Any]] = []

    def add(event: str, payload: dict[str, Any], *, display_channel: str, visibility: str, event_kind: str) -> None:
        clean_payload = _sanitize_public_payload({**payload, "display_channel": display_channel, "visibility": visibility, "event_kind": event_kind})
        events.append(
            {
                "event": event,
                "seq": len(events) + 1,
                "run_id": rid,
                "task_id": task,
                "timestamp": "",
                "display_channel": display_channel,
                "visibility": visibility,
                "event_kind": event_kind,
                "payload": clean_payload,
            }
        )

    projection = public.get("projection") or {}
    planner_result = public.get("planner_result") or {}
    add("run_started", {"runtime_status": "active", "provider_model": "not_reported"}, display_channel="status", visibility="progress", event_kind="task_progress")
    add("planner_started", {"planner_mode": _planner_mode(public), "schema_required": True}, display_channel="status", visibility="progress", event_kind="task_progress")
    add(
        "planner_plan",
        {"steps": public.get("plan") or [], "normalized_by_plan_schema": True, "planner_result": planner_result},
        display_channel="workbench",
        visibility="task_telemetry",
        event_kind="task_progress",
    )
    if public.get("active_model_policy"):
        add(
            "runtime_state",
            {"active_model_policy": public.get("active_model_policy"), "model_policy_active": True},
            display_channel="workbench",
            visibility="diagnostic",
            event_kind="task_progress",
        )
    if public.get("provider_status") and str(public.get("provider_status")) not in {"", "ready"}:
        add(
            "runtime_state",
            {"provider_status": public.get("provider_status"), "failure_kind": public.get("failure_kind", ""), "detail_policy": "diagnostic_summary_only"},
            display_channel="workbench",
            visibility="diagnostic",
            event_kind="task_progress",
        )
    pending_confirmations = _pending_confirmation_events(public, projection, rid=rid, task_id=task)
    for ticket in pending_confirmations:
        add(
            "approval_required",
            ticket,
            display_channel="workbench",
            visibility="task_telemetry",
            event_kind="approval_required",
        )
    for item in public.get("results") or []:
        add(
            "tool_started",
            {"step_id": item.get("step_id", ""), "tool_name": item.get("tool_name", "")},
            display_channel="workbench",
            visibility="task_telemetry",
            event_kind="tool_step",
        )
        add(
            "tool_result",
            {"step_id": item.get("step_id", ""), "tool_name": item.get("tool_name", ""), "status": item.get("status", ""), "audit_ref": item.get("audit_ref", ""), "output_summary": item.get("output_summary", "")},
            display_channel="workbench",
            visibility="task_telemetry",
            event_kind="tool_step",
        )
    if projection:
        add(
            "execution_report",
            {
                "status": projection.get("status", ""),
                "summary": projection.get("summary", ""),
                "artifacts": projection.get("artifacts", []),
                "failure_kind": public.get("failure_kind", ""),
                "next_action": public.get("next_action", ""),
                "final_output_contract": public.get("final_output_contract", "execution_report"),
                "adaptive_work_loop": public.get("adaptive_work_loop"),
                "context_window_bundle": public.get("context_window_bundle"),
                "skill_playbook_route": public.get("skill_playbook_route"),
                "active_model_policy": public.get("active_model_policy"),
            },
            display_channel="workbench",
            visibility="diagnostic" if projection.get("status") not in {"ok", "completed_pass", "completed_with_warnings"} else "artifact",
            event_kind="final",
        )
    for event in public.get("audit_events") or []:
        add(
            "audit_event",
            {"audit_id": event.get("audit_id") or event.get("audit_ref") or _stable_ref(event, prefix="audit"), "digest_only": True},
            display_channel="silent_audit",
            visibility="audit",
            event_kind="audit",
        )
    add(
        "assistant_final",
        {"content": _conversation_final_summary(public), "status": projection.get("status", "")},
        display_channel="conversation",
        visibility="user_dialogue",
        event_kind="final",
    )
    add(
        "run_terminal",
        {"terminal": True, "final_event_seen": True, "audit_count": projection.get("audit_count", 0), "status": projection.get("status", "")},
        display_channel="status",
        visibility="progress",
        event_kind="final",
    )
    return events



def _pending_confirmation_events(public: dict[str, Any], projection: dict[str, Any], *, rid: str, task_id: str) -> list[dict[str, Any]]:
    """生成前端 A5/人工确认弹窗所需的只读票据事件。

    真实审批动作仍必须回 Runtime；该事件只负责前端显示和用户确认入口。
    """
    pending = list(public.get("pending_confirmations") or [])
    status = str(projection.get("status") or public.get("status") or "")
    if not pending and status in {"blocked_A5", "awaiting_confirmation"}:
        pending = [
            {
                "ticket_id": _stable_ref({"run_id": rid, "task_id": task_id, "status": status}, prefix="confirm"),
                "tool_name": "QualityGate",
                "risk_level": "A5" if status == "blocked_A5" else "A4",
                "reason": public.get("failure_kind") or status or "requires_confirmation",
                "message": _conversation_final_summary(public),
                "arguments": {},
            }
        ]

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in pending:
        if not isinstance(raw, dict):
            continue
        ticket_id = str(raw.get("ticket_id") or raw.get("gate_id") or raw.get("approval_id") or "").strip()
        if not ticket_id:
            ticket_id = _stable_ref(raw, prefix="confirm")
        if ticket_id in seen:
            continue
        seen.add(ticket_id)
        risk_level = str(raw.get("risk_level") or ("A5" if status == "blocked_A5" else "A4") or "A4")
        message = str(raw.get("message") or raw.get("reason") or "检测到需要人工确认的高风险操作。")
        action_summary = str(raw.get("action_summary") or raw.get("title") or message)
        out.append(
            {
                "ticket_id": ticket_id,
                "gate_id": str(raw.get("gate_id") or ticket_id),
                "title": "需要人工确认" if risk_level.upper() == "A5" else "权限申请审批",
                "tool_name": str(raw.get("tool_name") or raw.get("source") or "QualityGate"),
                "source": str(raw.get("source") or raw.get("tool_name") or "Runtime / QualityGate"),
                "risk_level": risk_level,
                "decision": "requires_confirmation",
                "requires_user_confirmation": True,
                "action_summary": action_summary[:260],
                "impact_scope": str(raw.get("impact_scope") or raw.get("path") or "该操作存在高风险或不可逆影响，需用户确认后继续。")[:260],
                "message": message[:300],
                "audit_ref": str(raw.get("audit_ref") or ""),
                "rollback_ref": str(raw.get("rollback_ref") or ""),
                "frontend_contract": "tiangong.frontend.a5_approval.v1",
                "route_to_runtime_only": True,
                "detail_policy": "summary_only_no_raw_arguments",
            }
        )
    return out

def _conversation_final_summary(public: dict[str, Any]) -> str:
    projection = public.get("projection") or {}
    status = str(projection.get("status") or public.get("status") or "")
    artifacts = projection.get("artifacts") or []
    failure_kind = str(public.get("failure_kind") or "")
    if status in {"ok", "completed_pass", "deterministic_fallback"}:
        suffix = f"产物 {len(artifacts)} 个。" if artifacts else ""
        return ("任务已完成。" + suffix + "完整执行详情已放入任务工作台。").strip()
    if status == "completed_with_warnings":
        return "任务已完成，但存在非 A5 警告；完整质量门详情已放入任务工作台。"
    if failure_kind in {"weak_model_not_allowed", "model_policy_disabled", "tool_plan_blocked_by_model_policy"}:
        return "任务未执行：当前模型画像不能作为主脑完成该工作，或计划超出主动模型策略；详情已放入任务工作台。"
    if status in {"provider_not_ready", "model_required"} or failure_kind == "provider_not_ready":
        return "任务未执行：Provider / API Key / 模型未就绪。详情已放入任务工作台。"
    if status in {"blocked_A5", "awaiting_confirmation"}:
        return "任务等待人工确认：会话区只显示确认问题，详细风险和工具参数在任务工作台。"
    if status in {"failed_recoverable", "partial_with_resume", "partial_or_failed", "planner_failed"}:
        return "任务未完全完成，已生成可续接执行报告；详情已放入任务工作台。"
    return "任务已收口。完整执行报告已放入任务工作台。"


def validate_frontend_contract() -> FrontendContractCheck:
    issues: list[str] = []
    if TERMINAL_EVENT_ORDER[0] not in SSE_EVENT_TYPES or TERMINAL_EVENT_ORDER[1] not in SSE_EVENT_TYPES:
        issues.append("terminal event types missing")
    schema = build_runtime_sse_event_schema()
    required = set(schema.get("required_envelope_fields", []))
    for field in ("display_channel", "visibility", "event_kind"):
        if field not in required:
            issues.append(f"sse routing field missing: {field}")
    if STATUS_BAR_FIELDS != tuple(build_status_bar_fields_contract()["required_fields"]):
        issues.append("status bar fields drift")
    provider_contract = build_provider_settings_contract()
    forbidden = set(provider_contract["forbidden_response_fields"])
    if "api_key" not in forbidden or "base_url" not in forbidden:
        issues.append("provider plaintext fields not forbidden")
    if any(action not in FRONTEND_FORBIDDEN_ACTIONS for action in ("direct_provider_sdk_call", "direct_long_term_memory_write")):
        issues.append("critical frontend boundary missing")
    identity = build_product_identity_public()
    if identity.get("unique_developer") != "于泳翔" or identity.get("angel_investor") != "胖胖龙":
        issues.append("product identity drift")
    if identity.get("runtime_semantics") != "metadata_only":
        issues.append("product identity must stay metadata_only")
    return FrontendContractCheck(ok=not issues, issues=tuple(issues))


def _sanitize_public_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return sanitize_mapping({str(k): _sanitize_public_payload(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return [_sanitize_public_payload(item) for item in value]
    if isinstance(value, str):
        return _strip_sensitive_labels(redact_text(value))
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return _strip_sensitive_labels(redact_text(str(value)))


def _strip_sensitive_labels(text: str) -> str:
    text = re.sub(r"(?i)\b(api[_-]?key|apikey|token|secret|password|credential)\b\s*[:=]\s*<[^>]+>", "[redacted-secret]", text)
    text = re.sub(r"(?i)\b(raw[_-]?prompt|messages?)\b\s*[:=]\s*([^\s,;]+)", "[redacted-raw-prompt]", text)
    text = re.sub(r"(?i)\b(base_url|endpoint|endpoint_url|provider_base_url)\b\s*[:=]\s*<[^>]+>", "[redacted-endpoint]", text)
    text = re.sub(r"(?i)bearer\s+<[^>]+>", "Bearer [redacted-secret]", text)
    return text


def _stable_ref(payload: Any, *, prefix: str) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _planner_mode(public: dict[str, Any]) -> str:
    result = public.get("planner_result") or {}
    mode = result.get("source") or "rule_or_runtime"
    return str(mode)
