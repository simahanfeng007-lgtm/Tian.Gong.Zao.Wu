"""L1 五大模型高适配治理端口补丁。

本模块只定义 provider-neutral 的模型能力、供应方、调用信封和治理引用。
它不导入任何模型供应商 SDK，不调用网络，不保存明文凭据，也不做 provider 裁决。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping

L1_MODEL_GOVERNANCE_SCHEMA_VERSION = "0.1.hotfix3-five-model"

_PROVIDER_IDS = {"deepseek_v4", "mimo", "glm_5_1", "minimax_m3", "gpt_5_5"}
_FORBIDDEN_SECRET_MARKERS = ("mockkey_", "api-key", "apikey", "secret=", "bearer ")


class ModelProtocolFamily(str, Enum):
    """供应方协议族标识；只做描述，不代表真实连接能力。"""

    UNKNOWN = "unknown"
    OPENAI_CHAT_COMPLETIONS = "openai_chat_completions"
    OPENAI_RESPONSES = "openai_responses"
    ANTHROPIC_MESSAGES = "anthropic_messages"
    PROVIDER_NATIVE = "provider_native"
    LOCAL_SERVICE_PORT = "local_service_port"


class ModelCapabilityFlag(str, Enum):
    """通用能力标签；provider-specific 参数必须进入 descriptor。"""

    STREAMING = "streaming"
    TOOL_CALLING = "tool_calling"
    STRUCTURED_OUTPUT = "structured_output"
    JSON_MODE = "json_mode"
    REASONING_CONTROL = "reasoning_control"
    THINKING_MODE = "thinking_mode"
    MULTIMODAL_INPUT = "multimodal_input"
    FILE_INPUT = "file_input"
    IMAGE_INPUT = "image_input"
    AUDIO_INPUT = "audio_input"
    VIDEO_INPUT = "video_input"
    CONTEXT_CACHE = "context_cache"
    BATCH = "batch"
    LOCAL_DEPLOYMENT = "local_deployment"


def _ensure_short(value: str, field_name: str, limit: int = 256) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{field_name} must be a non-empty short string")


def _ensure_provider_id(value: str) -> None:
    if value not in _PROVIDER_IDS:
        raise ValueError(f"unsupported provider_id: {value}")


def _ensure_handle_only(value: str, field_name: str) -> None:
    _ensure_short(value, field_name)
    lowered = value.lower()
    if any(marker in lowered for marker in _FORBIDDEN_SECRET_MARKERS):
        raise ValueError(f"{field_name} must be a credential/reference handle, not plaintext secret material")


def _ensure_no_plain_secret_in_mapping(mapping: Mapping[str, Any], field_name: str) -> None:
    rendered = repr(mapping).lower()
    if any(marker in rendered for marker in _FORBIDDEN_SECRET_MARKERS):
        raise ValueError(f"{field_name} cannot contain plaintext credential material")


@dataclass(frozen=True, slots=True)
class ModelCredentialRequirementRef:
    """凭据需求引用。L1 只能持有 handle/ref。"""

    credential_handle_ref: str
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_handle_only(self.credential_handle_ref, "credential_handle_ref")


@dataclass(frozen=True, slots=True)
class ModelBudgetRequirementRef:
    """作用：表达五大模型治理端口的 ModelBudgetRequirementRef。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    budget_ref: str
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short(self.budget_ref, "budget_ref")


@dataclass(frozen=True, slots=True)
class ModelAuditRequirementRef:
    """作用：表达五大模型治理端口的 ModelAuditRequirementRef。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    audit_ref: str
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short(self.audit_ref, "audit_ref")


@dataclass(frozen=True, slots=True)
class ModelPolicyRequirementRef:
    """作用：表达五大模型治理端口的 ModelPolicyRequirementRef。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    policy_ref: str
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short(self.policy_ref, "policy_ref")


@dataclass(frozen=True, slots=True)
class ModelRoutingPreferenceRef:
    """作用：表达五大模型治理端口的 ModelRoutingPreferenceRef。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    routing_ref: str
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short(self.routing_ref, "routing_ref")


@dataclass(frozen=True, slots=True)
class ModelFallbackPolicyRef:
    """作用：表达五大模型治理端口的 ModelFallbackPolicyRef。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    fallback_ref: str
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short(self.fallback_ref, "fallback_ref")


@dataclass(frozen=True, slots=True)
class ModelStructuredOutputRequirement:
    """作用：表达五大模型治理端口的 ModelStructuredOutputRequirement。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    required: bool = False
    schema_ref: str | None = None
    strict: bool = False
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ModelReasoningRequirement:
    """作用：表达五大模型治理端口的 ModelReasoningRequirement。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    required: bool = False
    effort_hint: str = "unknown"
    expose_trace: bool = False
    trace_ref_only: bool = True
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.expose_trace and not self.trace_ref_only:
            raise ValueError("reasoning traces must remain ref-only at L1")


@dataclass(frozen=True, slots=True)
class ModelThinkingModeRequirement:
    """作用：表达五大模型治理端口的 ModelThinkingModeRequirement。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    required: bool = False
    mode_hint: str = "unknown"
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ModelMultimodalRequirement:
    """作用：表达五大模型治理端口的 ModelMultimodalRequirement。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    input_modalities: tuple[str, ...] = field(default_factory=tuple)
    output_modalities: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ModelStreamingRequirement:
    """作用：表达五大模型治理端口的 ModelStreamingRequirement。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    required: bool = False
    event_envelope_required: bool = True
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ModelProviderCapabilityDescriptor:
    """作用：表达五大模型治理端口的 ModelProviderCapabilityDescriptor。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    provider_id: str
    capability_flags: tuple[ModelCapabilityFlag, ...] = field(default_factory=tuple)
    context_window_tokens: int | str = "unknown"
    max_output_tokens: int | str = "unknown"
    provider_specific_parameters: Mapping[str, Any] = field(default_factory=dict)
    unknown_or_unverified_fields: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)
        _ensure_no_plain_secret_in_mapping(self.provider_specific_parameters, "provider_specific_parameters")
        if not self.unknown_or_unverified_fields:
            raise ValueError("unknown_or_unverified_fields must be explicit, use ('none',) when fully verified")


@dataclass(frozen=True, slots=True)
class ModelProviderRiskSurfaceDescriptor:
    """作用：表达五大模型治理端口的 ModelProviderRiskSurfaceDescriptor。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    provider_id: str
    credential_risk: str = "credential_handle_required"
    privacy_risk: str = "provider_data_boundary_required"
    cost_risk: str = "budget_required"
    streaming_risk: str = "stream_event_normalization_required"
    tool_call_risk: str = "tool_schema_exposure_policy_required"
    reasoning_trace_risk: str = "reasoning_trace_ref_only"
    unknown_or_unverified_fields: tuple[str, ...] = field(default_factory=lambda: ("none",))
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)


@dataclass(frozen=True, slots=True)
class ModelProviderDescriptor:
    """作用：表达五大模型治理端口的 ModelProviderDescriptor。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    provider_id: str
    provider_display_name: str
    protocol_families: tuple[ModelProtocolFamily, ...]
    capability_descriptor: ModelProviderCapabilityDescriptor
    risk_surface_descriptor: ModelProviderRiskSurfaceDescriptor
    credential_requirement_ref: ModelCredentialRequirementRef
    budget_requirement_ref: ModelBudgetRequirementRef
    audit_requirement_ref: ModelAuditRequirementRef
    policy_requirement_ref: ModelPolicyRequirementRef
    routing_preference_ref: ModelRoutingPreferenceRef | None = None
    fallback_policy_ref: ModelFallbackPolicyRef | None = None
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)
        _ensure_short(self.provider_display_name, "provider_display_name")
        if not self.protocol_families:
            raise ValueError("protocol_families cannot be empty")
        if self.capability_descriptor.provider_id != self.provider_id:
            raise ValueError("capability_descriptor provider mismatch")
        if self.risk_surface_descriptor.provider_id != self.provider_id:
            raise ValueError("risk_surface_descriptor provider mismatch")


@dataclass(frozen=True, slots=True)
class ModelProviderPort:
    """模型供应方端口。只暴露 provider-neutral 描述引用，不实现 provider SDK 或网络调用。"""

    provider_id: str
    provider_descriptor_ref: str
    capability_descriptor_ref: str | None = None
    risk_surface_descriptor_ref: str | None = None
    credential_requirement_ref: ModelCredentialRequirementRef | None = None
    budget_requirement_ref: ModelBudgetRequirementRef | None = None
    audit_requirement_ref: ModelAuditRequirementRef | None = None
    policy_requirement_ref: ModelPolicyRequirementRef | None = None
    provider_neutral_only: bool = True
    does_not_call_model: bool = True
    does_not_decide_provider: bool = True
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)
        _ensure_short(self.provider_descriptor_ref, "provider_descriptor_ref")
        if not self.provider_neutral_only or not self.does_not_call_model or not self.does_not_decide_provider:
            raise ValueError("ModelProviderPort is declaration-only at L1")


@dataclass(frozen=True, slots=True)
class ModelProviderRequirement:
    """作用：表达五大模型治理端口的 ModelProviderRequirement。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    allowed_provider_ids: tuple[str, ...] = field(default_factory=tuple)
    preferred_provider_ids: tuple[str, ...] = field(default_factory=tuple)
    excluded_provider_ids: tuple[str, ...] = field(default_factory=tuple)
    provider_descriptor_refs: tuple[str, ...] = field(default_factory=tuple)
    provider_selection_is_policy_hint_only: bool = True
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for provider_id in self.allowed_provider_ids + self.preferred_provider_ids + self.excluded_provider_ids:
            _ensure_provider_id(provider_id)
        if self.provider_selection_is_policy_hint_only is not True:
            raise ValueError("L1 provider requirement cannot decide provider selection")


@dataclass(frozen=True, slots=True)
class ModelCapabilityRequirement:
    """作用：表达五大模型治理端口的 ModelCapabilityRequirement。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    requirement_id: str
    task_kind: str = "unknown"
    provider_requirement: ModelProviderRequirement | None = None
    streaming: ModelStreamingRequirement = field(default_factory=ModelStreamingRequirement)
    structured_output: ModelStructuredOutputRequirement = field(default_factory=ModelStructuredOutputRequirement)
    reasoning: ModelReasoningRequirement = field(default_factory=ModelReasoningRequirement)
    thinking_mode: ModelThinkingModeRequirement = field(default_factory=ModelThinkingModeRequirement)
    multimodal: ModelMultimodalRequirement = field(default_factory=ModelMultimodalRequirement)
    credential_requirement_ref: ModelCredentialRequirementRef | None = None
    budget_requirement_ref: ModelBudgetRequirementRef | None = None
    audit_requirement_ref: ModelAuditRequirementRef | None = None
    policy_requirement_ref: ModelPolicyRequirementRef | None = None
    routing_preference_ref: ModelRoutingPreferenceRef | None = None
    fallback_policy_ref: ModelFallbackPolicyRef | None = None
    provider_specific_capability_hints: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short(self.requirement_id, "requirement_id")
        _ensure_no_plain_secret_in_mapping(self.provider_specific_capability_hints, "provider_specific_capability_hints")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ModelContextEnvelope:
    """作用：表达五大模型治理端口的 ModelContextEnvelope。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    context_ref: str
    assembled_by_layer: str = "L3"
    visible_context_only: bool = True
    raw_context_not_embedded: bool = True
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short(self.context_ref, "context_ref")
        if self.raw_context_not_embedded is not True:
            raise ValueError("L1 ModelContextEnvelope must not embed raw provider context")


@dataclass(frozen=True, slots=True)
class ModelToolSchemaEnvelope:
    """作用：表达五大模型治理端口的 ModelToolSchemaEnvelope。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    tool_schema_ref: str
    exposed_by_layer: str = "L3"
    policy_checked_by_l5: bool = False
    raw_tool_implementation_not_embedded: bool = True
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short(self.tool_schema_ref, "tool_schema_ref")
        if self.raw_tool_implementation_not_embedded is not True:
            raise ValueError("tool schema envelope cannot embed tool implementation")


@dataclass(frozen=True, slots=True)
class ModelInvocationPort:
    """模型调用端口。只承载调用 envelope/ref，不拼装 provider 请求、不执行模型。"""

    invocation_port_id: str
    capability_requirement_ref: str
    context_envelope_ref: str
    provider_requirement_ref: str | None = None
    policy_requirement_ref: ModelPolicyRequirementRef | None = None
    budget_requirement_ref: ModelBudgetRequirementRef | None = None
    audit_requirement_ref: ModelAuditRequirementRef | None = None
    credential_requirement_ref: ModelCredentialRequirementRef | None = None
    dispatch_by_l3_required: bool = True
    permit_by_l5_required: bool = True
    adapter_by_l4_required: bool = True
    provider_neutral_only: bool = True
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short(self.invocation_port_id, "invocation_port_id")
        _ensure_short(self.capability_requirement_ref, "capability_requirement_ref")
        _ensure_short(self.context_envelope_ref, "context_envelope_ref")
        if not (self.dispatch_by_l3_required and self.permit_by_l5_required and self.adapter_by_l4_required):
            raise ValueError("ModelInvocationPort must preserve L3/L5/L4 governance chain")
        if not self.provider_neutral_only:
            raise ValueError("ModelInvocationPort is provider-neutral at L1")


@dataclass(frozen=True, slots=True)
class ModelInvocationEnvelope:
    """作用：表达五大模型治理端口的 ModelInvocationEnvelope。边界：只保存协议/引用，不调用模型、不持有明文凭据。"""
    invocation_id: str
    capability_requirement: ModelCapabilityRequirement
    context_envelope: ModelContextEnvelope
    tool_schema_envelope: ModelToolSchemaEnvelope | None = None
    permit_ref: str | None = None
    dispatch_request_ref: str | None = None
    provider_descriptor_ref: str | None = None
    provider_neutral_only: bool = True
    schema_version: str = L1_MODEL_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short(self.invocation_id, "invocation_id")
        if self.provider_neutral_only is not True:
            raise ValueError("L1 invocation envelope must remain provider-neutral")
