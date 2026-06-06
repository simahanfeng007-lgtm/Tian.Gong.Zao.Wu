"""L2 五大模型交互状态事实补丁。

本模块只记录模型调用事实、状态引用、用量、延迟、失败、回退、流式和工具调用状态。
它不调用模型、不选择 provider、不分配预算、不读取凭据、不保存完整原始响应正文。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping

L2_MODEL_INTERACTION_SCHEMA_VERSION = "0.1.hotfix2-five-model"
_PROVIDER_IDS = {"deepseek_v4", "mimo", "glm_5_1", "minimax_m3", "gpt_5_5", "unknown"}


class ModelInvocationPhase(str, Enum):
    """作用：记录五大模型交互事实的 ModelInvocationPhase。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    UNKNOWN = "unknown"
    PLANNED = "planned"
    POLICY_CHECK_REQUESTED = "policy_check_requested"
    CREDENTIAL_CHECK_REQUESTED = "credential_check_requested"
    BUDGET_CHECK_REQUESTED = "budget_check_requested"
    AUDIT_CHECK_REQUESTED = "audit_check_requested"
    PERMIT_GRANTED = "permit_granted"
    DISPATCHED_TO_L4 = "dispatched_to_l4"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"
    FALLBACK_RECORDED = "fallback_recorded"


class ModelProviderHealth(str, Enum):
    """作用：记录五大模型交互事实的 ModelProviderHealth。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    DEGRADED = "degraded"
    RATE_LIMITED = "rate_limited"
    DISABLED_BY_DEFAULT = "disabled_by_default"
    BLOCKED_BY_POLICY = "blocked_by_policy"


def _ensure_provider_id(provider_id: str) -> None:
    if provider_id not in _PROVIDER_IDS:
        raise ValueError(f"unsupported provider_id: {provider_id}")


def _ensure_ref_only(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ValueError(f"{field_name} must be a non-empty short reference")
    lowered = value.lower()
    if "sk-" in lowered or "bearer " in lowered or "secret=" in lowered:
        raise ValueError(f"{field_name} must not contain plaintext secret material")


@dataclass(frozen=True, slots=True)
class ProviderFactsheetStateRef:
    """作用：记录五大模型交互事实的 ProviderFactsheetStateRef。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    provider_id: str
    factsheet_ref: str
    verified_at: str = "unknown"
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)
        _ensure_ref_only(self.factsheet_ref, "factsheet_ref")


@dataclass(frozen=True, slots=True)
class ModelCredentialStateRef:
    """作用：记录五大模型交互事实的 ModelCredentialStateRef。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    credential_handle_ref: str
    redacted: bool = True
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref_only(self.credential_handle_ref, "credential_handle_ref")
        if self.redacted is not True:
            raise ValueError("credential state must remain redacted")


@dataclass(frozen=True, slots=True)
class ModelBudgetStateRef:
    """作用：记录五大模型交互事实的 ModelBudgetStateRef。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    budget_ref: str
    reserved_tokens_ref: str | None = None
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref_only(self.budget_ref, "budget_ref")


@dataclass(frozen=True, slots=True)
class ModelAuditStateRef:
    """作用：记录五大模型交互事实的 ModelAuditStateRef。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    audit_ref: str
    audit_required: bool = True
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref_only(self.audit_ref, "audit_ref")


@dataclass(frozen=True, slots=True)
class ModelProviderState:
    """作用：记录五大模型交互事实的 ModelProviderState。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    provider_id: str
    model_id: str = "unknown"
    health: ModelProviderHealth = ModelProviderHealth.UNKNOWN
    factsheet_state_ref: ProviderFactsheetStateRef | None = None
    descriptor_ref: str | None = None
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)


@dataclass(frozen=True, slots=True)
class ModelContextWindowState:
    """作用：记录五大模型交互事实的 ModelContextWindowState。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    provider_id: str = "unknown"
    context_window_tokens: int | None = None
    input_tokens_observed: int | None = None
    output_token_limit_observed: int | None = None
    overflow_risk: bool = False
    compression_suggestion_ref: str | None = None
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)
        for value in (self.context_window_tokens, self.input_tokens_observed, self.output_token_limit_observed):
            if value is not None and value < 0:
                raise ValueError("token counts must be non-negative")


@dataclass(frozen=True, slots=True)
class ModelTokenUsageState:
    """作用：记录五大模型交互事实的 ModelTokenUsageState。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_input_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    usage_ref_only: bool = True
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value in (self.prompt_tokens, self.completion_tokens, self.cached_input_tokens, self.reasoning_tokens, self.total_tokens):
            if value < 0:
                raise ValueError("token usage must be non-negative")
        if self.usage_ref_only is not True:
            raise ValueError("token usage must remain state/ref only")


@dataclass(frozen=True, slots=True)
class ModelLatencyState:
    """作用：记录五大模型交互事实的 ModelLatencyState。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    first_token_ms: int | None = None
    total_latency_ms: int | None = None
    provider_queue_ms: int | None = None
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value in (self.first_token_ms, self.total_latency_ms, self.provider_queue_ms):
            if value is not None and value < 0:
                raise ValueError("latency values must be non-negative")


@dataclass(frozen=True, slots=True)
class ModelFailureState:
    """作用：记录五大模型交互事实的 ModelFailureState。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    provider_id: str = "unknown"
    error_code: str = "unknown"
    error_class: str = "unknown"
    retryable: bool = False
    failure_ref: str | None = None
    raw_error_body_ref: str | None = None
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)
        if self.raw_error_body_ref is not None:
            _ensure_ref_only(self.raw_error_body_ref, "raw_error_body_ref")


@dataclass(frozen=True, slots=True)
class ModelFallbackState:
    """作用：记录五大模型交互事实的 ModelFallbackState。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    attempted: bool = False
    from_provider_id: str = "unknown"
    to_provider_id: str = "unknown"
    fallback_plan_ref: str | None = None
    fallback_result_ref: str | None = None
    executed_by_l4_with_l5_permit: bool = False
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.from_provider_id)
        _ensure_provider_id(self.to_provider_id)


@dataclass(frozen=True, slots=True)
class ModelStreamingState:
    """作用：记录五大模型交互事实的 ModelStreamingState。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    requested: bool = False
    started: bool = False
    event_count: int = 0
    stream_event_ref: str | None = None
    normalized_envelope_only: bool = True
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.event_count < 0:
            raise ValueError("event_count must be non-negative")
        if self.normalized_envelope_only is not True:
            raise ValueError("streaming state must use normalized envelope only")


@dataclass(frozen=True, slots=True)
class ModelToolCallState:
    """作用：记录五大模型交互事实的 ModelToolCallState。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    tool_call_count: int = 0
    tool_schema_ref: str | None = None
    normalized_tool_call_ref: str | None = None
    raw_provider_tool_call_not_stored: bool = True
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.tool_call_count < 0:
            raise ValueError("tool_call_count must be non-negative")
        if self.raw_provider_tool_call_not_stored is not True:
            raise ValueError("raw provider tool calls must not be stored in L2")


@dataclass(frozen=True, slots=True)
class ModelStructuredOutputState:
    """作用：记录五大模型交互事实的 ModelStructuredOutputState。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    requested: bool = False
    schema_ref: str | None = None
    valid: bool | None = None
    validation_result_ref: str | None = None
    raw_output_ref: str | None = None
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.raw_output_ref is not None:
            _ensure_ref_only(self.raw_output_ref, "raw_output_ref")


@dataclass(frozen=True, slots=True)
class ModelReasoningTraceStateRef:
    """作用：记录五大模型交互事实的 ModelReasoningTraceStateRef。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    trace_ref: str | None = None
    redacted: bool = True
    plaintext_trace_not_stored: bool = True
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.trace_ref is not None:
            _ensure_ref_only(self.trace_ref, "trace_ref")
        if not self.redacted or not self.plaintext_trace_not_stored:
            raise ValueError("reasoning trace must remain redacted/ref-only")


@dataclass(frozen=True, slots=True)
class ModelOutputSafetyState:
    """作用：记录五大模型交互事实的 ModelOutputSafetyState。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    refusal_detected: bool = False
    refusal_shape: str = "unknown"
    safety_label_refs: tuple[str, ...] = ()
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ModelCapabilityState:
    """作用：记录五大模型交互事实的 ModelCapabilityState。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    provider_id: str = "unknown"
    capability_flags_observed: tuple[str, ...] = ()
    unknown_capabilities: tuple[str, ...] = ("unknown",)
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)


@dataclass(frozen=True, slots=True)
class ModelInvocationState:
    """作用：记录五大模型交互事实的 ModelInvocationState。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    invocation_state_id: str
    invocation_phase: ModelInvocationPhase = ModelInvocationPhase.UNKNOWN
    provider_state: ModelProviderState = field(default_factory=lambda: ModelProviderState(provider_id="unknown"))
    context_window_state: ModelContextWindowState = field(default_factory=ModelContextWindowState)
    token_usage_state: ModelTokenUsageState = field(default_factory=ModelTokenUsageState)
    latency_state: ModelLatencyState = field(default_factory=ModelLatencyState)
    failure_state: ModelFailureState | None = None
    fallback_state: ModelFallbackState | None = None
    streaming_state: ModelStreamingState = field(default_factory=ModelStreamingState)
    tool_call_state: ModelToolCallState = field(default_factory=ModelToolCallState)
    structured_output_state: ModelStructuredOutputState = field(default_factory=ModelStructuredOutputState)
    reasoning_trace_state_ref: ModelReasoningTraceStateRef = field(default_factory=ModelReasoningTraceStateRef)
    credential_state_ref: ModelCredentialStateRef | None = None
    budget_state_ref: ModelBudgetStateRef | None = None
    audit_state_ref: ModelAuditStateRef | None = None
    output_safety_state: ModelOutputSafetyState = field(default_factory=ModelOutputSafetyState)
    capability_state: ModelCapabilityState = field(default_factory=ModelCapabilityState)
    response_body_ref: str | None = None
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref_only(self.invocation_state_id, "invocation_state_id")
        if self.response_body_ref is not None:
            _ensure_ref_only(self.response_body_ref, "response_body_ref")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ModelInteractionState:
    """作用：记录五大模型交互事实的 ModelInteractionState。边界：只保存状态事实，不执行模型调用、不做策略裁决。"""
    interaction_state_id: str
    invocation_states: tuple[ModelInvocationState, ...] = field(default_factory=tuple)
    provider_factsheet_state_refs: tuple[ProviderFactsheetStateRef, ...] = field(default_factory=tuple)
    state_is_fact_only: bool = True
    no_execution_logic: bool = True
    schema_version: str = L2_MODEL_INTERACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref_only(self.interaction_state_id, "interaction_state_id")
        if not self.state_is_fact_only or not self.no_execution_logic:
            raise ValueError("L2 ModelInteractionState can only record facts")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
