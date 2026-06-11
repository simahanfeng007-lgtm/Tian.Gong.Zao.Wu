"""L4 五大模型 provider-neutral adapter 补丁。

L4 是真实模型 API 适配的承载位置，但本 hotfix 只提供：
- 官方文档 factsheet 与 capability profile；
- provider-neutral mapper/envelope；
- 五个 provider 的 disabled stub 与 live skeleton；
- 无 L5 permit 时默认拒绝，且所有 skeleton 均不发网络请求。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable

L4_MODEL_PROVIDER_SCHEMA_VERSION = "0.1.hotfix3-five-model"
VERIFIED_AT = "2026-06-05"
PROVIDER_IDS = ("deepseek_v4", "mimo", "glm_5_1", "minimax_m3", "gpt_5_5")


def _ensure_provider_id(provider_id: str) -> None:
    if provider_id not in PROVIDER_IDS:
        raise ValueError(f"unsupported provider_id: {provider_id}")


def _ensure_ref(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        raise ValueError(f"{field_name} must be a non-empty short string/ref")
    lowered = value.lower()
    if "mockkey_" in lowered or "bearer " in lowered or "secret=" in lowered:
        raise ValueError(f"{field_name} cannot contain plaintext secret material")


@dataclass(frozen=True, slots=True)
class ProviderFactsheet:
    provider_id: str
    provider_display_name: str
    official_doc_url_ref: str
    verified_at: str
    supported_model_ids: tuple[str, ...]
    default_model_id: str
    protocol_family: tuple[str, ...]
    base_url_ref: str
    auth_scheme_ref: str
    credential_handle_required: bool
    request_api_style: str
    streaming_supported: bool | str
    tool_calling_supported: bool | str
    structured_output_supported: bool | str
    json_mode_supported: bool | str
    reasoning_control_supported: bool | str
    thinking_mode_supported: bool | str
    multimodal_input_supported: bool | str
    file_input_supported: bool | str
    image_input_supported: bool | str
    audio_input_supported: bool | str
    video_input_supported: bool | str
    context_window_tokens: int | str
    max_output_tokens: int | str
    cache_supported: bool | str
    batch_supported: bool | str
    rate_limit_policy_ref: str
    pricing_policy_ref: str
    safety_refusal_shape: str
    error_code_shape: str
    retry_policy_hint: str
    fallback_compatibility: str
    local_deployment_supported: bool | str
    provider_specific_parameters: Mapping[str, Any] = field(default_factory=dict)
    known_deprecations: tuple[str, ...] = field(default_factory=tuple)
    unknown_or_unverified_fields: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)
        if not self.unknown_or_unverified_fields:
            raise ValueError("unknown_or_unverified_fields must be explicit")
        if not self.credential_handle_required:
            raise ValueError("all five providers must require credential handle")
        rendered = repr(self.provider_specific_parameters).lower()
        if "mockkey_" in rendered or "bearer " in rendered or "secret=" in rendered:
            raise ValueError("provider_specific_parameters cannot contain plaintext secret material")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ModelProviderCapabilityProfile:
    provider_id: str
    factsheet: ProviderFactsheet
    capability_flags: tuple[str, ...]
    provider_specific_parameters: Mapping[str, Any] = field(default_factory=dict)
    unknown_or_unverified_fields: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)
        if self.factsheet.provider_id != self.provider_id:
            raise ValueError("factsheet/provider mismatch")
        if not self.unknown_or_unverified_fields:
            raise ValueError("unknown_or_unverified_fields must be explicit")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ModelProviderAdapterDescriptor:
    provider_id: str
    display_name: str
    default_model_id: str
    supported_model_ids: tuple[str, ...]
    protocol_family: tuple[str, ...]
    capability_profile_ref: str
    disabled_by_default: bool = True
    requires_l5_permit: bool = True
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)
        if not self.disabled_by_default or not self.requires_l5_permit:
            raise ValueError("model adapters must be disabled-by-default and require L5 permit")


@dataclass(frozen=True, slots=True)
class ModelProviderCredentialHandleRef:
    credential_handle_ref: str
    provider_id: str
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.credential_handle_ref, "credential_handle_ref")
        _ensure_provider_id(self.provider_id)


@dataclass(frozen=True, slots=True)
class ModelProviderBudgetEnvelope:
    budget_permit_ref: str
    provider_id: str
    readonly_budget_ref: bool = True
    does_not_decide_budget: bool = True
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.budget_permit_ref, "budget_permit_ref")
        _ensure_provider_id(self.provider_id)
        if not self.readonly_budget_ref or not self.does_not_decide_budget:
            raise ValueError("L4 budget envelope can only reference L5 budget")


@dataclass(frozen=True, slots=True)
class ModelProviderAuditEnvelope:
    audit_requirement_ref: str
    provider_id: str
    readonly_audit_ref: bool = True
    does_not_write_audit: bool = True
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.audit_requirement_ref, "audit_requirement_ref")
        _ensure_provider_id(self.provider_id)
        if not self.readonly_audit_ref or not self.does_not_write_audit:
            raise ValueError("L4 audit envelope can only reference L5 audit")


@dataclass(frozen=True, slots=True)
class ModelProviderPolicyEnvelope:
    policy_permit_ref: str
    provider_id: str
    readonly_policy_ref: bool = True
    does_not_decide_policy: bool = True
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.policy_permit_ref, "policy_permit_ref")
        _ensure_provider_id(self.provider_id)
        if not self.readonly_policy_ref or not self.does_not_decide_policy:
            raise ValueError("L4 policy envelope can only reference L5 policy")


@dataclass(frozen=True, slots=True)
class ModelContextInputEnvelope:
    context_ref: str
    prompt_ref: str | None = None
    tool_schema_ref: str | None = None
    raw_prompt_not_embedded: bool = True
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.context_ref, "context_ref")
        if not self.raw_prompt_not_embedded:
            raise ValueError("L4 context input envelope must remain ref-only in this patch")


@dataclass(frozen=True, slots=True)
class ModelOutputEnvelope:
    provider_id: str
    model_id: str
    output_ref: str
    tool_call_refs: tuple[str, ...] = ()
    structured_output_ref: str | None = None
    usage_ref: str | None = None
    normalized_only: bool = True
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)
        _ensure_ref(self.output_ref, "output_ref")
        if not self.normalized_only:
            raise ValueError("model outputs must be normalized envelopes")


@dataclass(frozen=True, slots=True)
class ModelStreamEventEnvelope:
    provider_id: str
    event_type: str
    event_ref: str
    sequence: int = 0
    normalized_only: bool = True
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)
        _ensure_ref(self.event_ref, "event_ref")
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        if not self.normalized_only:
            raise ValueError("stream events must be normalized")


@dataclass(frozen=True, slots=True)
class ModelProviderFailureEnvelope:
    provider_id: str
    failure_code: str
    failure_class: str
    retryable: bool = False
    details_ref: str = "failure-ref:disabled-by-default"
    requires_l5_permit: bool = True
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)
        _ensure_ref(self.failure_code, "failure_code")
        _ensure_ref(self.failure_class, "failure_class")
        _ensure_ref(self.details_ref, "details_ref")


@dataclass(frozen=True, slots=True)
class ModelFallbackResultEnvelope:
    from_provider_id: str
    to_provider_id: str
    result_ref: str
    executed: bool = False
    executed_with_l5_permit: bool = False
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.from_provider_id)
        _ensure_provider_id(self.to_provider_id)
        _ensure_ref(self.result_ref, "result_ref")
        if self.executed and not self.executed_with_l5_permit:
            raise ValueError("fallback execution requires L5 permit")


@dataclass(frozen=True, slots=True)
class ModelProviderRequestMapper:
    provider_id: str
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)

    def map_request(self, dispatch_request: Any) -> dict[str, Any]:
        """Return a provider-neutral fake mapping; never sends HTTP."""
        return {
            "provider_id": self.provider_id,
            "dispatch_request_ref": getattr(dispatch_request, "dispatch_request_ref", "unknown"),
            "provider_specific_http_not_sent": True,
            "requires_l5_permit": True,
        }


@dataclass(frozen=True, slots=True)
class ModelProviderResponseMapper:
    provider_id: str
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)

    def map_response(self, fake_response_ref: str = "response-ref:fake") -> ModelOutputEnvelope:
        return ModelOutputEnvelope(provider_id=self.provider_id, model_id="test-only", output_ref=fake_response_ref)


@dataclass(frozen=True, slots=True)
class ModelProviderStreamMapper:
    provider_id: str
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)

    def map_event(self, fake_event_ref: str = "stream-ref:fake", sequence: int = 0) -> ModelStreamEventEnvelope:
        return ModelStreamEventEnvelope(provider_id=self.provider_id, event_type="fake_delta", event_ref=fake_event_ref, sequence=sequence)


@dataclass(frozen=True, slots=True)
class ModelProviderToolCallMapper:
    provider_id: str
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)

    def normalize_tool_call(self, fake_tool_call: Mapping[str, Any]) -> dict[str, Any]:
        tool_call_id = fake_tool_call["id"] if "id" in fake_tool_call else "unknown"
        name = fake_tool_call["name"] if "name" in fake_tool_call else "unknown"
        arguments_ref = fake_tool_call["arguments_ref"] if "arguments_ref" in fake_tool_call else "arguments-ref:unknown"
        return {
            "provider_id": self.provider_id,
            "tool_call_id": str(tool_call_id),
            "name": str(name),
            "arguments_ref": str(arguments_ref),
            "raw_arguments_not_embedded": True,
        }


@dataclass(frozen=True, slots=True)
class ModelProviderStructuredOutputMapper:
    provider_id: str
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)

    def normalize_structured_output(self, output_ref: str) -> dict[str, Any]:
        _ensure_ref(output_ref, "output_ref")
        return {"provider_id": self.provider_id, "structured_output_ref": output_ref, "normalized_only": True}


@dataclass(frozen=True, slots=True)
class ModelProviderReasoningMapper:
    provider_id: str
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)

    def normalize_reasoning_ref(self, trace_ref: str = "reasoning-ref:redacted") -> dict[str, Any]:
        _ensure_ref(trace_ref, "trace_ref")
        return {"provider_id": self.provider_id, "reasoning_trace_ref": trace_ref, "plaintext_trace_not_stored": True}


@dataclass(frozen=True, slots=True)
class ModelProviderErrorMapper:
    provider_id: str
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)

    def map_error(self, error_code: str = "unknown", retryable: bool = False) -> ModelProviderFailureEnvelope:
        return ModelProviderFailureEnvelope(
            provider_id=self.provider_id,
            failure_code=error_code,
            failure_class="provider_failure",
            retryable=retryable,
            details_ref=f"failure-ref:{self.provider_id}:{error_code}",
        )


@dataclass(frozen=True, slots=True)
class ModelProviderRetryPolicyHint:
    provider_id: str
    retryable_error_codes: tuple[str, ...]
    non_retryable_error_codes: tuple[str, ...]
    advisory_only: bool = True
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)
        if not self.advisory_only:
            raise ValueError("retry policy is hint-only in L4")


@runtime_checkable
class ModelProviderAdapterProtocol(Protocol):
    provider_id: str

    def invoke(self, context: ModelContextInputEnvelope, permit: Any | None = None) -> ModelOutputEnvelope | ModelProviderFailureEnvelope: ...

    def stream(self, context: ModelContextInputEnvelope, permit: Any | None = None) -> tuple[ModelStreamEventEnvelope, ...] | ModelProviderFailureEnvelope: ...


@dataclass(slots=True)
class ModelProviderAdapterRegistry:
    adapters: dict[str, ModelProviderAdapterProtocol] = field(default_factory=dict)

    def register(self, adapter: ModelProviderAdapterProtocol) -> None:
        _ensure_provider_id(adapter.provider_id)
        self.adapters[adapter.provider_id] = adapter

    def get(self, provider_id: str) -> ModelProviderAdapterProtocol:
        _ensure_provider_id(provider_id)
        return self.adapters[provider_id]


class ModelProviderMultimodalMapper(ModelProviderRequestMapper):
    def map_multimodal_refs(self, modality_refs: Mapping[str, str]) -> dict[str, str]:
        return {key: value for key, value in modality_refs.items()}


MIMO_API_SURFACES = ("token_plan_api", "ordinary_api")


def _ensure_mimo_api_surface(api_surface: str) -> None:
    if api_surface not in MIMO_API_SURFACES:
        raise ValueError(f"unsupported MiMo api_surface: {api_surface}")


@dataclass(frozen=True, slots=True)
class MiMoApiSurfaceDescriptor:
    """MiMo API 面选择描述。只表达 plan / 普通 API 引用，不保存 endpoint 或 key。"""

    api_surface: str
    endpoint_ref: str
    credential_scope_ref: str
    provider_id: str = "mimo"
    endpoint_is_ref_only: bool = True
    credential_is_handle_only: bool = True
    selected_by_l5_scope: bool = True
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)
        _ensure_mimo_api_surface(self.api_surface)
        _ensure_ref(self.endpoint_ref, "endpoint_ref")
        _ensure_ref(self.credential_scope_ref, "credential_scope_ref")
        if not self.endpoint_is_ref_only or not self.credential_is_handle_only or not self.selected_by_l5_scope:
            raise ValueError("MiMo api surface must remain L5-scoped ref-only")


def mimo_api_surface_descriptors() -> dict[str, MiMoApiSurfaceDescriptor]:
    return {
        "token_plan_api": MiMoApiSurfaceDescriptor(
            api_surface="token_plan_api",
            endpoint_ref="endpoint-ref:mimo:token-plan-api",
            credential_scope_ref="credential-scope-ref:mimo:token-plan-api",
        ),
        "ordinary_api": MiMoApiSurfaceDescriptor(
            api_surface="ordinary_api",
            endpoint_ref="endpoint-ref:mimo:ordinary-api",
            credential_scope_ref="credential-scope-ref:mimo:ordinary-api",
        ),
    }


@dataclass(frozen=True, slots=True)
class ModelProviderLongContextGuard:
    provider_id: str
    context_window_tokens: int | str
    schema_version: str = L4_MODEL_PROVIDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_provider_id(self.provider_id)

    def assess(self, estimated_input_tokens: int) -> dict[str, Any]:
        if estimated_input_tokens < 0:
            raise ValueError("estimated_input_tokens must be non-negative")
        if isinstance(self.context_window_tokens, int):
            return {
                "provider_id": self.provider_id,
                "estimated_input_tokens": estimated_input_tokens,
                "context_window_tokens": self.context_window_tokens,
                "overflow_risk": estimated_input_tokens > self.context_window_tokens,
            }
        return {"provider_id": self.provider_id, "estimated_input_tokens": estimated_input_tokens, "context_window_tokens": "unknown", "overflow_risk": "unknown"}


# ---- provider factsheets ----------------------------------------------------

def provider_factsheet_deepseek_v4() -> ProviderFactsheet:
    return ProviderFactsheet(
        provider_id="deepseek_v4",
        provider_display_name="DeepSeek V4",
        official_doc_url_ref="https://api-docs.deepseek.com/news/news260424",
        verified_at=VERIFIED_AT,
        supported_model_ids=("deepseek-v4-flash", "deepseek-v4-pro"),
        default_model_id="deepseek-v4-flash",
        protocol_family=("openai_chat_completions", "anthropic_messages"),
        base_url_ref="official-ref:deepseek-base-url-openai-and-anthropic",
        auth_scheme_ref="credential-handle:bearer",
        credential_handle_required=True,
        request_api_style="OpenAI Chat Completions compatible / Anthropic compatible",
        streaming_supported=True,
        tool_calling_supported=True,
        structured_output_supported=True,
        json_mode_supported=True,
        reasoning_control_supported=True,
        thinking_mode_supported=True,
        multimodal_input_supported="unknown",
        file_input_supported="unknown",
        image_input_supported="unknown",
        audio_input_supported="unknown",
        video_input_supported="unknown",
        context_window_tokens=1_000_000,
        max_output_tokens="384K",
        cache_supported=True,
        batch_supported="unknown",
        rate_limit_policy_ref="official-ref:deepseek-rate-limit-concurrency-and-429",
        pricing_policy_ref="official-ref:deepseek-models-pricing-v4",
        safety_refusal_shape="unknown",
        error_code_shape="HTTP status + provider error message",
        retry_policy_hint="retry transient 5xx/503/429 with L5 budget; never retry auth/balance/invalid params",
        fallback_compatibility="OpenAI-compatible branch can fall back to compatible text/tool-call providers when L5 permits",
        local_deployment_supported=False,
        provider_specific_parameters={"thinking": "supported", "strict_tool_mode": "supported", "context_caching": "default_on"},
        known_deprecations=("deepseek-chat and deepseek-reasoner retire after 2026-07-24 15:59 UTC per official V4 notice",),
        unknown_or_unverified_fields=("multimodal_input_supported", "file_input_supported", "image_input_supported", "audio_input_supported", "video_input_supported", "batch_supported", "safety_refusal_shape"),
    )


def provider_factsheet_mimo() -> ProviderFactsheet:
    return ProviderFactsheet(
        provider_id="mimo",
        provider_display_name="Xiaomi MiMo",
        official_doc_url_ref=(
            "https://mimo.mi.com/; "
            "https://platform.xiaomimimo.com/docs/en-US/quick-start/model; "
            "https://platform.xiaomimimo.com/docs/en-US/updates/model; "
            "https://platform.xiaomimimo.com/docs/en-US/price/pay-as-you-go; "
            "https://platform.xiaomimimo.com/docs/en-US/price/tokenplan/quick-access; "
            "https://platform.xiaomimimo.com/docs/en-US/price/tokenplan/price-comparison; "
            "https://platform.xiaomimimo.com/docs/en-US/quick-start/error-codes; "
            "https://platform.xiaomimimo.com/docs/en-US/quick-start/model-hyperparameters"
        ),
        verified_at=VERIFIED_AT,
        supported_model_ids=("mimo-v2.5-pro", "mimo-v2.5", "mimo-v2.5-asr", "mimo-v2-flash", "mimo-v2-pro", "mimo-v2-omni"),
        default_model_id="mimo-v2.5-pro",
        protocol_family=("provider_native", "openai_chat_completions:api-platform-compatible", "local_service_port"),
        base_url_ref="official-ref:mimo-api-platform; supports token_plan_api and ordinary_api via credential scoped endpoint ref, never hardcoded",
        auth_scheme_ref="credential-handle:token_plan_api_or_ordinary_api",
        credential_handle_required=True,
        request_api_style="MiMo API Platform; supports token_plan_api and ordinary_api; open-weight local service port reservation",
        streaming_supported=True,
        tool_calling_supported=True,
        structured_output_supported=True,
        json_mode_supported="unknown",
        reasoning_control_supported=True,
        thinking_mode_supported="unknown",
        multimodal_input_supported=True,
        file_input_supported="unknown",
        image_input_supported=True,
        audio_input_supported=True,
        video_input_supported=True,
        context_window_tokens=1_000_000,
        max_output_tokens=128_000,
        cache_supported=True,
        batch_supported="unknown",
        rate_limit_policy_ref="official-ref:mimo-model-and-rate-limits; per-model RPM/TPM and account concurrency; 429 on excess",
        pricing_policy_ref="official-ref:mimo-pay-as-you-go-and-token-plan-pricing; ordinary API and Token Plan credentials are independent",
        safety_refusal_shape="unknown",
        error_code_shape="HTTP status table 400/401/402/403/404/421/429/500/503 with MiMo platform error guidance",
        retry_policy_hint="unknown; only L5-governed transient retry allowed after factsheet refresh",
        fallback_compatibility="token_plan_api, ordinary_api, or open-weight local branch only through L3/L5/L4 envelopes",
        local_deployment_supported=True,
        provider_specific_parameters={
            "api_surfaces": ("token_plan_api", "ordinary_api"),
            "model_id_case_policy": "all MiMo model ids are normalized to lowercase",
            "token_plan_multiplier": "v2.5=1x; v2.5-pro=2x",
            "token_plan_key_format_ref": "official token-plan key prefix; token_plan_api only; cannot be mixed with ordinary API",
            "ordinary_api_key_format_ref": "official ordinary-api key prefix; pay-as-you-go API only; cannot be mixed with Token Plan",
            "official_refs": {
                "model_and_rate_limits": "https://platform.xiaomimimo.com/docs/en-US/quick-start/model",
                "model_release": "https://platform.xiaomimimo.com/docs/en-US/updates/model",
                "pay_as_you_go_pricing": "https://platform.xiaomimimo.com/docs/en-US/price/pay-as-you-go",
                "token_plan_quick_access": "https://platform.xiaomimimo.com/docs/en-US/price/tokenplan/quick-access",
                "token_plan_price_comparison": "https://platform.xiaomimimo.com/docs/en-US/price/tokenplan/price-comparison",
                "error_codes": "https://platform.xiaomimimo.com/docs/en-US/quick-start/error-codes",
                "model_hyperparameters": "https://platform.xiaomimimo.com/docs/en-US/quick-start/model-hyperparameters"
            },
            "local_open_weight": "supported via service port only",
            "api_surface_selection": "selected by L5 credential/provider scope, not by plugin code",
        },
        known_deprecations=(),
        unknown_or_unverified_fields=("json_mode_supported", "thinking_mode_supported", "file_input_supported", "batch_supported", "ordinary_api_exact_endpoint", "safety_refusal_shape"),
    )


def provider_factsheet_glm_5_1() -> ProviderFactsheet:
    return ProviderFactsheet(
        provider_id="glm_5_1",
        provider_display_name="Z.AI GLM-5.1",
        official_doc_url_ref="https://docs.z.ai/cn/guides/llm/glm-5.1; https://docs.z.ai/cn/api-reference/model-api",
        verified_at=VERIFIED_AT,
        supported_model_ids=("glm-5.1",),
        default_model_id="glm-5.1",
        protocol_family=("openai_chat_completions", "provider_native"),
        base_url_ref="official-ref:zai-general-and-coding-paas-v4-endpoints",
        auth_scheme_ref="credential-handle:bearer",
        credential_handle_required=True,
        request_api_style="OpenAI-compatible chat.completions with Z.AI parameters",
        streaming_supported=True,
        tool_calling_supported=True,
        structured_output_supported=True,
        json_mode_supported="unknown",
        reasoning_control_supported=True,
        thinking_mode_supported=True,
        multimodal_input_supported=False,
        file_input_supported="unknown",
        image_input_supported=False,
        audio_input_supported=False,
        video_input_supported=False,
        context_window_tokens=200_000,
        max_output_tokens=131_072,
        cache_supported=True,
        batch_supported="unknown",
        rate_limit_policy_ref="official-ref:zai-quota/rate-limit unknown in public factsheet",
        pricing_policy_ref="official-ref:zai-glm-5.1-pricing-input-cached-output",
        safety_refusal_shape="unknown",
        error_code_shape="HTTP status + Z.AI error code/message",
        retry_policy_hint="retry transient 5xx/429 only under L5 budget; do not retry auth/invalid params",
        fallback_compatibility="OpenAI-compatible text/function-call provider fallback if L5 permits",
        local_deployment_supported=False,
        provider_specific_parameters={"thinking.type": "enabled/disabled", "tool_stream": "supported", "coding_endpoint": "separate endpoint"},
        known_deprecations=(),
        unknown_or_unverified_fields=("json_mode_supported", "file_input_supported", "batch_supported", "rate_limit_policy_ref", "safety_refusal_shape"),
    )


def provider_factsheet_minimax_m3() -> ProviderFactsheet:
    return ProviderFactsheet(
        provider_id="minimax_m3",
        provider_display_name="MiniMax M3",
        official_doc_url_ref="https://platform.minimax.io/docs/guides/models-intro; https://platform.minimax.io/docs/guides/text-ai-coding-tools; https://platform.minimax.io/docs/guides/pricing-token-plan",
        verified_at=VERIFIED_AT,
        supported_model_ids=("MiniMax-M3",),
        default_model_id="MiniMax-M3",
        protocol_family=("openai_chat_completions", "anthropic_messages", "provider_native"),
        base_url_ref="official-ref:minimax-openai-v1-and-anthropic-base-url",
        auth_scheme_ref="credential-handle:bearer",
        credential_handle_required=True,
        request_api_style="OpenAI-compatible or Anthropic-compatible chat/messages",
        streaming_supported=True,
        tool_calling_supported=True,
        structured_output_supported="unknown",
        json_mode_supported="unknown",
        reasoning_control_supported=True,
        thinking_mode_supported=True,
        multimodal_input_supported=True,
        file_input_supported="unknown",
        image_input_supported=True,
        audio_input_supported="unknown",
        video_input_supported=True,
        context_window_tokens=1_000_000,
        max_output_tokens="recommended 128K; max 512K per official parameter docs",
        cache_supported=True,
        batch_supported="unknown",
        rate_limit_policy_ref="official-ref:minimax-rpm-tpm-rate-limit-definitions",
        pricing_policy_ref="official-ref:minimax-m3-pay-as-you-go-pricing",
        safety_refusal_shape="unknown",
        error_code_shape="HTTP status + MiniMax error body/code",
        retry_policy_hint="retry transient 5xx/429 under L5 budget; do not retry invalid/auth errors",
        fallback_compatibility="OpenAI/Anthropic-compatible coding/agentic fallback when L5 permits",
        local_deployment_supported=False,
        provider_specific_parameters={"thinking": "supported", "reasoning_split": "OpenAI-compatible option", "strict_model_name": "MiniMax-M3"},
        known_deprecations=(),
        unknown_or_unverified_fields=("structured_output_supported", "json_mode_supported", "file_input_supported", "audio_input_supported", "batch_supported", "safety_refusal_shape"),
    )


def provider_factsheet_gpt_5_5() -> ProviderFactsheet:
    return ProviderFactsheet(
        provider_id="gpt_5_5",
        provider_display_name="OpenAI GPT-5.5",
        official_doc_url_ref="https://developers.openai.com/api/docs/models/gpt-5.5; https://developers.openai.com/api/docs/guides/latest-model; https://developers.openai.com/api/docs/pricing",
        verified_at=VERIFIED_AT,
        supported_model_ids=("gpt-5.5",),
        default_model_id="gpt-5.5",
        protocol_family=("openai_responses", "openai_chat_completions:compatibility_unknown"),
        base_url_ref="official-ref:openai-responses-api-base-url",
        auth_scheme_ref="credential-handle:bearer",
        credential_handle_required=True,
        request_api_style="OpenAI Responses API",
        streaming_supported=True,
        tool_calling_supported=True,
        structured_output_supported=True,
        json_mode_supported=True,
        reasoning_control_supported=True,
        thinking_mode_supported=False,
        multimodal_input_supported=True,
        file_input_supported=True,
        image_input_supported=True,
        audio_input_supported="unknown",
        video_input_supported="unknown",
        context_window_tokens=1_050_000,
        max_output_tokens=128_000,
        cache_supported=True,
        batch_supported=True,
        rate_limit_policy_ref="official-ref:openai-rate-limits-account-tier-dependent",
        pricing_policy_ref="official-ref:openai-gpt-5.5-pricing",
        safety_refusal_shape="Responses API refusal/output envelope",
        error_code_shape="HTTP status + OpenAI error object",
        retry_policy_hint="retry transient 5xx/429 after L5 budget/rate permit; do not retry auth/invalid request",
        fallback_compatibility="OpenAI Responses-compatible fallback via L3/L5/L4 envelopes",
        local_deployment_supported=False,
        provider_specific_parameters={"reasoning.effort": "none/low/medium/high/xhigh", "tools": "functions/web/file/computer_use", "prompt_cache_retention": "supported"},
        known_deprecations=(),
        unknown_or_unverified_fields=("openai_chat_completions_compatibility", "audio_input_supported", "video_input_supported", "rate_limit_policy_ref_exact_numbers"),
    )


_PROVIDER_FACTSHEET_BUILDERS = {
    "deepseek_v4": provider_factsheet_deepseek_v4,
    "mimo": provider_factsheet_mimo,
    "glm_5_1": provider_factsheet_glm_5_1,
    "minimax_m3": provider_factsheet_minimax_m3,
    "gpt_5_5": provider_factsheet_gpt_5_5,
}


def all_provider_factsheets() -> dict[str, ProviderFactsheet]:
    return {provider_id: builder() for provider_id, builder in _PROVIDER_FACTSHEET_BUILDERS.items()}


def _capability_flags(f: ProviderFactsheet) -> tuple[str, ...]:
    flags: list[str] = []
    for name in (
        "streaming_supported", "tool_calling_supported", "structured_output_supported", "json_mode_supported",
        "reasoning_control_supported", "thinking_mode_supported", "multimodal_input_supported", "file_input_supported",
        "image_input_supported", "audio_input_supported", "video_input_supported", "cache_supported", "batch_supported",
    ):
        value = getattr(f, name)
        if value is True:
            flags.append(name.replace("_supported", ""))
        elif value == "unknown":
            flags.append(name.replace("_supported", "") + ":unknown")
    if f.local_deployment_supported is True:
        flags.append("local_deployment")
    elif f.local_deployment_supported == "unknown":
        flags.append("local_deployment:unknown")
    return tuple(flags)


def capability_profile_for(provider_id: str) -> ModelProviderCapabilityProfile:
    f = all_provider_factsheets()[provider_id]
    return ModelProviderCapabilityProfile(
        provider_id=provider_id,
        factsheet=f,
        capability_flags=_capability_flags(f),
        provider_specific_parameters=f.provider_specific_parameters,
        unknown_or_unverified_fields=f.unknown_or_unverified_fields,
    )


def descriptor_for(provider_id: str) -> ModelProviderAdapterDescriptor:
    f = all_provider_factsheets()[provider_id]
    return ModelProviderAdapterDescriptor(
        provider_id=f.provider_id,
        display_name=f.provider_display_name,
        default_model_id=f.default_model_id,
        supported_model_ids=f.supported_model_ids,
        protocol_family=f.protocol_family,
        capability_profile_ref=f"provider-capability-profile:{f.provider_id}",
    )


def provider_capability_matrix() -> dict[str, dict[str, Any]]:
    return {pid: {"model_ids": fs.supported_model_ids, "context_window_tokens": fs.context_window_tokens, "max_output_tokens": fs.max_output_tokens, "capability_flags": _capability_flags(fs), "unknown": fs.unknown_or_unverified_fields} for pid, fs in all_provider_factsheets().items()}


def provider_endpoint_matrix() -> dict[str, dict[str, Any]]:
    return {pid: {"base_url_ref": fs.base_url_ref, "protocol_family": fs.protocol_family, "request_api_style": fs.request_api_style, "auth_scheme_ref": fs.auth_scheme_ref} for pid, fs in all_provider_factsheets().items()}


def provider_feature_gap_matrix() -> dict[str, dict[str, Any]]:
    return {pid: {"unknown_or_unverified_fields": fs.unknown_or_unverified_fields, "fallback_compatibility": fs.fallback_compatibility} for pid, fs in all_provider_factsheets().items()}


def provider_risk_surface_matrix() -> dict[str, dict[str, str]]:
    return {pid: {"credential": "credential_handle_required", "budget": "l5_budget_permit_required", "audit": "l5_audit_required", "policy": "l5_policy_required", "raw_response": "normalize_to_l4_envelope", "live_call": "disabled_without_l5_permit"} for pid in PROVIDER_IDS}


def provider_budget_matrix() -> dict[str, dict[str, Any]]:
    return {pid: {"pricing_policy_ref": fs.pricing_policy_ref, "cache_supported": fs.cache_supported, "budget_envelope": f"l5-budget-permit-ref:{pid}"} for pid, fs in all_provider_factsheets().items()}


def provider_error_taxonomy_matrix() -> dict[str, dict[str, Any]]:
    return {pid: {"error_code_shape": fs.error_code_shape, "retry_policy_hint": fs.retry_policy_hint, "standard_failure_envelope": f"ModelProviderFailureEnvelope:{pid}"} for pid, fs in all_provider_factsheets().items()}


# ---- provider-specific classes --------------------------------------------
class DeepSeekV4ProviderDescriptor(ModelProviderAdapterDescriptor):
    def __init__(self) -> None: super().__init__(**asdict(descriptor_for("deepseek_v4")))
class MiMoProviderDescriptor(ModelProviderAdapterDescriptor):
    def __init__(self) -> None: super().__init__(**asdict(descriptor_for("mimo")))
class GLM51ProviderDescriptor(ModelProviderAdapterDescriptor):
    def __init__(self) -> None: super().__init__(**asdict(descriptor_for("glm_5_1")))
class MiniMaxM3ProviderDescriptor(ModelProviderAdapterDescriptor):
    def __init__(self) -> None: super().__init__(**asdict(descriptor_for("minimax_m3")))
class GPT55ProviderDescriptor(ModelProviderAdapterDescriptor):
    def __init__(self) -> None: super().__init__(**asdict(descriptor_for("gpt_5_5")))

class DeepSeekV4CapabilityProfile(ModelProviderCapabilityProfile):
    def __init__(self) -> None: super().__init__(**asdict(capability_profile_for("deepseek_v4")))
class MiMoCapabilityProfile(ModelProviderCapabilityProfile):
    def __init__(self) -> None: super().__init__(**asdict(capability_profile_for("mimo")))
class GLM51CapabilityProfile(ModelProviderCapabilityProfile):
    def __init__(self) -> None: super().__init__(**asdict(capability_profile_for("glm_5_1")))
class MiniMaxM3CapabilityProfile(ModelProviderCapabilityProfile):
    def __init__(self) -> None: super().__init__(**asdict(capability_profile_for("minimax_m3")))
class GPT55CapabilityProfile(ModelProviderCapabilityProfile):
    def __init__(self) -> None: super().__init__(**asdict(capability_profile_for("gpt_5_5")))

class DeepSeekV4RequestMapper(ModelProviderRequestMapper):
    def __init__(self) -> None: super().__init__("deepseek_v4")
class DeepSeekV4ResponseMapper(ModelProviderResponseMapper):
    def __init__(self) -> None: super().__init__("deepseek_v4")
class DeepSeekV4StreamMapper(ModelProviderStreamMapper):
    def __init__(self) -> None: super().__init__("deepseek_v4")
class DeepSeekV4ToolCallMapper(ModelProviderToolCallMapper):
    def __init__(self) -> None: super().__init__("deepseek_v4")
class DeepSeekV4ReasoningMapper(ModelProviderReasoningMapper):
    def __init__(self) -> None: super().__init__("deepseek_v4")
class DeepSeekV4ErrorMapper(ModelProviderErrorMapper):
    def __init__(self) -> None: super().__init__("deepseek_v4")

class MiMoRequestMapper(ModelProviderRequestMapper):
    def __init__(self) -> None: super().__init__("mimo")

    def map_request(self, dispatch_request: Any, api_surface: str = "ordinary_api") -> dict[str, Any]:
        _ensure_mimo_api_surface(api_surface)
        mapped = super().map_request(dispatch_request)
        surface = mimo_api_surface_descriptors()[api_surface]
        mapped.update({
            "api_surface": surface.api_surface,
            "endpoint_ref": surface.endpoint_ref,
            "credential_scope_ref": surface.credential_scope_ref,
            "supports_token_plan_and_ordinary_api": True,
            "model_ids_lowercase_only": True,
        })
        return mapped


class MiMoTokenPlanRequestMapper(MiMoRequestMapper):
    def map_request(self, dispatch_request: Any) -> dict[str, Any]:
        return super().map_request(dispatch_request, api_surface="token_plan_api")


class MiMoOrdinaryApiRequestMapper(MiMoRequestMapper):
    def map_request(self, dispatch_request: Any) -> dict[str, Any]:
        return super().map_request(dispatch_request, api_surface="ordinary_api")


class MiMoResponseMapper(ModelProviderResponseMapper):
    def __init__(self) -> None: super().__init__("mimo")
class MiMoStreamMapper(ModelProviderStreamMapper):
    def __init__(self) -> None: super().__init__("mimo")
class MiMoToolCallMapper(ModelProviderToolCallMapper):
    def __init__(self) -> None: super().__init__("mimo")
class MiMoMultimodalMapper(ModelProviderMultimodalMapper):
    def __init__(self) -> None: super().__init__("mimo")
class MiMoLongContextGuard(ModelProviderLongContextGuard):
    def __init__(self) -> None: super().__init__("mimo", 1_000_000)
class MiMoErrorMapper(ModelProviderErrorMapper):
    def __init__(self) -> None: super().__init__("mimo")

class GLM51RequestMapper(ModelProviderRequestMapper):
    def __init__(self) -> None: super().__init__("glm_5_1")
class GLM51ResponseMapper(ModelProviderResponseMapper):
    def __init__(self) -> None: super().__init__("glm_5_1")
class GLM51StreamMapper(ModelProviderStreamMapper):
    def __init__(self) -> None: super().__init__("glm_5_1")
class GLM51ToolCallMapper(ModelProviderToolCallMapper):
    def __init__(self) -> None: super().__init__("glm_5_1")
class GLM51ThinkingModeMapper(ModelProviderReasoningMapper):
    def __init__(self) -> None: super().__init__("glm_5_1")
class GLM51StructuredOutputMapper(ModelProviderStructuredOutputMapper):
    def __init__(self) -> None: super().__init__("glm_5_1")
class GLM51ErrorMapper(ModelProviderErrorMapper):
    def __init__(self) -> None: super().__init__("glm_5_1")

class MiniMaxM3RequestMapper(ModelProviderRequestMapper):
    def __init__(self) -> None: super().__init__("minimax_m3")
class MiniMaxM3ResponseMapper(ModelProviderResponseMapper):
    def __init__(self) -> None: super().__init__("minimax_m3")
class MiniMaxM3StreamMapper(ModelProviderStreamMapper):
    def __init__(self) -> None: super().__init__("minimax_m3")
class MiniMaxM3ToolCallMapper(ModelProviderToolCallMapper):
    def __init__(self) -> None: super().__init__("minimax_m3")
class MiniMaxM3MultimodalMapper(ModelProviderMultimodalMapper):
    def __init__(self) -> None: super().__init__("minimax_m3")
class MiniMaxM3LongContextGuard(ModelProviderLongContextGuard):
    def __init__(self) -> None: super().__init__("minimax_m3", 1_000_000)
class MiniMaxM3ErrorMapper(ModelProviderErrorMapper):
    def __init__(self) -> None: super().__init__("minimax_m3")

class GPT55RequestMapper(ModelProviderRequestMapper):
    def __init__(self) -> None: super().__init__("gpt_5_5")
class GPT55ResponseMapper(ModelProviderResponseMapper):
    def __init__(self) -> None: super().__init__("gpt_5_5")
class GPT55StreamMapper(ModelProviderStreamMapper):
    def __init__(self) -> None: super().__init__("gpt_5_5")
class GPT55ToolCallMapper(ModelProviderToolCallMapper):
    def __init__(self) -> None: super().__init__("gpt_5_5")
class GPT55StructuredOutputMapper(ModelProviderStructuredOutputMapper):
    def __init__(self) -> None: super().__init__("gpt_5_5")
class GPT55ReasoningMapper(ModelProviderReasoningMapper):
    def __init__(self) -> None: super().__init__("gpt_5_5")
class GPT55MultimodalMapper(ModelProviderMultimodalMapper):
    def __init__(self) -> None: super().__init__("gpt_5_5")
class GPT55ErrorMapper(ModelProviderErrorMapper):
    def __init__(self) -> None: super().__init__("gpt_5_5")


class _DisabledModelAdapter:
    provider_id: str

    def __init__(self, provider_id: str) -> None:
        _ensure_provider_id(provider_id)
        self.provider_id = provider_id

    def invoke(self, context: ModelContextInputEnvelope, permit: Any | None = None) -> ModelOutputEnvelope | ModelProviderFailureEnvelope:
        if permit is None:
            return ModelProviderFailureEnvelope(provider_id=self.provider_id, failure_code="l5_permit_required", failure_class="disabled_by_default")
        return ModelProviderFailureEnvelope(provider_id=self.provider_id, failure_code="live_adapter_disabled", failure_class="disabled_by_default")

    def stream(self, context: ModelContextInputEnvelope, permit: Any | None = None) -> tuple[ModelStreamEventEnvelope, ...] | ModelProviderFailureEnvelope:
        if permit is None:
            return ModelProviderFailureEnvelope(provider_id=self.provider_id, failure_code="l5_permit_required", failure_class="disabled_by_default")
        return ModelProviderFailureEnvelope(provider_id=self.provider_id, failure_code="live_adapter_disabled", failure_class="disabled_by_default")


class DeepSeekV4DisabledStub(_DisabledModelAdapter):
    def __init__(self) -> None: super().__init__("deepseek_v4")
class DeepSeekV4LiveAdapterSkeleton(DeepSeekV4DisabledStub): pass
class MiMoDisabledStub(_DisabledModelAdapter):
    def __init__(self) -> None: super().__init__("mimo")
class MiMoLiveAdapterSkeleton(MiMoDisabledStub): pass
class MiMoLocalAdapterSkeleton(MiMoDisabledStub): pass
class GLM51DisabledStub(_DisabledModelAdapter):
    def __init__(self) -> None: super().__init__("glm_5_1")
class GLM51LiveAdapterSkeleton(GLM51DisabledStub): pass
class MiniMaxM3DisabledStub(_DisabledModelAdapter):
    def __init__(self) -> None: super().__init__("minimax_m3")
class MiniMaxM3LiveAdapterSkeleton(MiniMaxM3DisabledStub): pass
class GPT55DisabledStub(_DisabledModelAdapter):
    def __init__(self) -> None: super().__init__("gpt_5_5")
class GPT55LiveAdapterSkeleton(GPT55DisabledStub): pass


def build_default_disabled_registry() -> ModelProviderAdapterRegistry:
    registry = ModelProviderAdapterRegistry()
    for adapter in (DeepSeekV4DisabledStub(), MiMoDisabledStub(), GLM51DisabledStub(), MiniMaxM3DisabledStub(), GPT55DisabledStub()):
        registry.register(adapter)
    return registry
