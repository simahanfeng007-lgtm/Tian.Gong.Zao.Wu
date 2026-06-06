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
    "tool_started",
    "tool_result",
    "audit_event",
    "assistant_delta",
    "assistant_final",
    "run_terminal",
    "error",
)

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
    """Provider 设置页契约。API Key/base_url 是写入型输入，不作为明文返回字段。"""
    return {
        "schema": CONTRACT_VERSION,
        "endpoint": SETTINGS_ENDPOINT,
        "read_fields": list(PROVIDER_SETTING_FIELDS),
        "write_only_fields": ["api_key", "base_url"],
        "forbidden_response_fields": ["api_key", "authorization", "bearer", "token", "secret", "base_url", "endpoint"],
        "storage_boundary": "gateway_or_controlled_config_layer_only",
        "frontend_storage": {"local_storage_plaintext": False, "logs_plaintext": False},
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
    """将 RuntimeRunResult 投影为冻结 SSE 顺序样本。\n\n该函数只读 result 的公共摘要，不执行任何工具。assistant_final 必须先于\nrun_terminal，供前端做无刷新续答与收口判断。\n"""
    public = runtime_result_to_public_dict(result)
    rid = run_id or _stable_ref(public, prefix="run")
    events: list[dict[str, Any]] = []

    def add(event: str, payload: dict[str, Any]) -> None:
        events.append({"event": event, "seq": len(events) + 1, "run_id": rid, "task_id": task_id, "payload": _sanitize_public_payload(payload)})

    projection = public.get("projection") or {}
    add("run_started", {"runtime_status": "active", "provider_model": "not_reported"})
    add("planner_started", {"planner_mode": _planner_mode(public), "schema_required": True})
    add("planner_plan", {"steps": public.get("plan") or [], "normalized_by_plan_schema": True})
    for item in public.get("results") or []:
        add("tool_started", {"step_id": item.get("step_id", ""), "tool_name": item.get("tool_name", "")})
        add("tool_result", {"step_id": item.get("step_id", ""), "status": item.get("status", ""), "audit_ref": item.get("audit_ref", "")})
    for event in public.get("audit_events") or []:
        add("audit_event", {"audit_id": event.get("audit_id") or event.get("audit_ref") or _stable_ref(event, prefix="audit"), "digest_only": True})
    add("assistant_final", {"content": projection.get("summary", ""), "status": projection.get("status", "")})
    add("run_terminal", {"terminal": True, "final_event_seen": True, "audit_count": projection.get("audit_count", 0)})
    return events


def validate_frontend_contract() -> FrontendContractCheck:
    issues: list[str] = []
    if TERMINAL_EVENT_ORDER[0] not in SSE_EVENT_TYPES or TERMINAL_EVENT_ORDER[1] not in SSE_EVENT_TYPES:
        issues.append("terminal event types missing")
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
