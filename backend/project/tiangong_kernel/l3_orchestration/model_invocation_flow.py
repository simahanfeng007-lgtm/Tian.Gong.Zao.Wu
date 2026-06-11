"""L3 五大模型调用编排补丁。

本模块只表达模型调用意图、上下文/提示词装配请求、L5 治理检查请求、L4 派发请求和回退/重规划建议。
它不导入 provider SDK，不拼 provider-specific HTTP body，不直接调用模型，不执行 fallback。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping

L3_MODEL_INVOCATION_SCHEMA_VERSION = "0.1.hotfix2-five-model"
_PROVIDER_IDS = {"deepseek_v4", "mimo", "glm_5_1", "minimax_m3", "gpt_5_5", "unknown"}


class ModelInvocationRequestKind(str, Enum):
    CALL = "call"
    STREAM = "stream"
    TOOL_CALL = "tool_call"
    STRUCTURED_OUTPUT = "structured_output"


def _ensure_ref(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ValueError(f"{field_name} must be a non-empty short reference")
    lowered = value.lower()
    if "mockkey_" in lowered or "bearer " in lowered or "secret=" in lowered:
        raise ValueError(f"{field_name} cannot contain secret material")


def _ensure_provider_id(provider_id: str) -> None:
    if provider_id not in _PROVIDER_IDS:
        raise ValueError(f"unsupported provider_id: {provider_id}")


def _ensure_provider_tuple(provider_ids: tuple[str, ...]) -> None:
    for provider_id in provider_ids:
        _ensure_provider_id(provider_id)


@dataclass(frozen=True, slots=True)
class ModelInvocationPlanRef:
    plan_ref: str
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.plan_ref, "plan_ref")


@dataclass(frozen=True, slots=True)
class ModelInvocationStepRef:
    step_ref: str
    plan_ref: ModelInvocationPlanRef | None = None
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.step_ref, "step_ref")


@dataclass(frozen=True, slots=True)
class ModelBudgetCheckRequest:
    budget_request_ref: str
    capability_requirement_ref: str
    provider_candidates: tuple[str, ...] = ("unknown",)
    request_only: bool = True
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.budget_request_ref, "budget_request_ref")
        _ensure_ref(self.capability_requirement_ref, "capability_requirement_ref")
        _ensure_provider_tuple(self.provider_candidates)
        if self.request_only is not True:
            raise ValueError("L3 budget request cannot allocate budget")


@dataclass(frozen=True, slots=True)
class ModelCredentialNeedRef:
    credential_need_ref: str
    provider_candidates: tuple[str, ...] = ("unknown",)
    handle_only: bool = True
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.credential_need_ref, "credential_need_ref")
        _ensure_provider_tuple(self.provider_candidates)
        if self.handle_only is not True:
            raise ValueError("L3 can only request credential handles")


@dataclass(frozen=True, slots=True)
class ModelAuditNeedRef:
    audit_need_ref: str
    provider_candidates: tuple[str, ...] = ("unknown",)
    audit_required: bool = True
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.audit_need_ref, "audit_need_ref")
        _ensure_provider_tuple(self.provider_candidates)


@dataclass(frozen=True, slots=True)
class ModelPolicyCheckRequest:
    policy_request_ref: str
    capability_requirement_ref: str
    provider_candidates: tuple[str, ...] = ("unknown",)
    request_only: bool = True
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.policy_request_ref, "policy_request_ref")
        _ensure_ref(self.capability_requirement_ref, "capability_requirement_ref")
        _ensure_provider_tuple(self.provider_candidates)
        if self.request_only is not True:
            raise ValueError("L3 policy request cannot make policy decisions")


@dataclass(frozen=True, slots=True)
class ModelProviderRankingHint:
    ranking_hint_ref: str
    ranked_provider_ids: tuple[str, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    provider_selection_decision: bool = False
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.ranking_hint_ref, "ranking_hint_ref")
        _ensure_provider_tuple(self.ranked_provider_ids)
        if self.advisory_only is not True or self.provider_selection_decision is not False:
            raise ValueError("provider ranking is hint only, not a decision")


@dataclass(frozen=True, slots=True)
class ModelFallbackPlanRef:
    fallback_plan_ref: str
    provider_chain: tuple[str, ...] = field(default_factory=tuple)
    plan_ref_only: bool = True
    executes_fallback: bool = False
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.fallback_plan_ref, "fallback_plan_ref")
        _ensure_provider_tuple(self.provider_chain)
        if not self.plan_ref_only or self.executes_fallback:
            raise ValueError("L3 fallback can only be plan/ref/suggestion")


@dataclass(frozen=True, slots=True)
class ModelContextAssemblyRequest:
    context_request_ref: str
    capability_requirement_ref: str
    max_context_tokens_hint: int | None = None
    assembled_context_ref_expected: bool = True
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.context_request_ref, "context_request_ref")
        _ensure_ref(self.capability_requirement_ref, "capability_requirement_ref")
        if self.max_context_tokens_hint is not None and self.max_context_tokens_hint < 0:
            raise ValueError("max_context_tokens_hint must be non-negative")


@dataclass(frozen=True, slots=True)
class ModelPromptAssemblyRequest:
    prompt_request_ref: str
    context_request_ref: str
    prompt_template_ref: str | None = None
    raw_prompt_not_embedded: bool = True
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.prompt_request_ref, "prompt_request_ref")
        _ensure_ref(self.context_request_ref, "context_request_ref")
        if self.raw_prompt_not_embedded is not True:
            raise ValueError("L3 prompt request must remain ref-only")


@dataclass(frozen=True, slots=True)
class ModelToolSchemaExposureRequest:
    tool_schema_request_ref: str
    capability_requirement_ref: str
    tool_schema_ref: str | None = None
    requires_l5_policy_check: bool = True
    raw_tool_implementation_not_exposed: bool = True
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.tool_schema_request_ref, "tool_schema_request_ref")
        _ensure_ref(self.capability_requirement_ref, "capability_requirement_ref")
        if not self.requires_l5_policy_check or not self.raw_tool_implementation_not_exposed:
            raise ValueError("tool schema exposure must remain L5 checked and implementation-free")


@dataclass(frozen=True, slots=True)
class ModelIntent:
    intent_ref: str
    capability_requirement_ref: str
    candidate_provider_ids: tuple[str, ...] = ("unknown",)
    context_assembly_request: ModelContextAssemblyRequest | None = None
    prompt_assembly_request: ModelPromptAssemblyRequest | None = None
    tool_schema_exposure_request: ModelToolSchemaExposureRequest | None = None
    provider_ranking_hint: ModelProviderRankingHint | None = None
    fallback_plan_ref: ModelFallbackPlanRef | None = None
    l5_policy_check_request: ModelPolicyCheckRequest | None = None
    l5_budget_check_request: ModelBudgetCheckRequest | None = None
    l5_credential_need_ref: ModelCredentialNeedRef | None = None
    l5_audit_need_ref: ModelAuditNeedRef | None = None
    llm_remains_main_controller: bool = True
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.intent_ref, "intent_ref")
        _ensure_ref(self.capability_requirement_ref, "capability_requirement_ref")
        _ensure_provider_tuple(self.candidate_provider_ids)
        if self.llm_remains_main_controller is not True:
            raise ValueError("L3 cannot replace the LLM main controller")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ModelCallDispatchRequest:
    dispatch_request_ref: str
    intent_ref: str
    capability_requirement_ref: str
    context_envelope_ref: str
    provider_candidates: tuple[str, ...]
    l5_policy_check_request: ModelPolicyCheckRequest
    l5_budget_check_request: ModelBudgetCheckRequest
    l5_credential_need_ref: ModelCredentialNeedRef
    l5_audit_need_ref: ModelAuditNeedRef
    permit_ref: str | None = None
    request_kind: ModelInvocationRequestKind = ModelInvocationRequestKind.CALL
    provider_specific_http_body_not_built: bool = True
    no_live_call: bool = True
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.dispatch_request_ref, "dispatch_request_ref")
        _ensure_ref(self.intent_ref, "intent_ref")
        _ensure_ref(self.capability_requirement_ref, "capability_requirement_ref")
        _ensure_ref(self.context_envelope_ref, "context_envelope_ref")
        _ensure_provider_tuple(self.provider_candidates)
        if self.provider_specific_http_body_not_built is not True or self.no_live_call is not True:
            raise ValueError("L3 dispatch requests cannot build provider HTTP bodies or live calls")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ModelStreamDispatchRequest(ModelCallDispatchRequest):
    request_kind: ModelInvocationRequestKind = ModelInvocationRequestKind.STREAM
    stream_event_envelope_required: bool = True


@dataclass(frozen=True, slots=True)
class ModelToolCallDispatchRequest(ModelCallDispatchRequest):
    request_kind: ModelInvocationRequestKind = ModelInvocationRequestKind.TOOL_CALL
    tool_schema_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ModelStructuredOutputDispatchRequest(ModelCallDispatchRequest):
    request_kind: ModelInvocationRequestKind = ModelInvocationRequestKind.STRUCTURED_OUTPUT
    structured_schema_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ModelProviderSwitchSuggestion:
    suggestion_ref: str
    from_provider_id: str
    to_provider_id: str
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    executes_switch: bool = False
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.suggestion_ref, "suggestion_ref")
        _ensure_provider_id(self.from_provider_id)
        _ensure_provider_id(self.to_provider_id)
        if not self.advisory_only or self.executes_switch:
            raise ValueError("provider switch is only a suggestion at L3")


@dataclass(frozen=True, slots=True)
class ModelFallbackSuggestion:
    suggestion_ref: str
    fallback_plan_ref: ModelFallbackPlanRef
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    executes_fallback: bool = False
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.suggestion_ref, "suggestion_ref")
        if not self.advisory_only or self.executes_fallback:
            raise ValueError("fallback is only a suggestion at L3")


@dataclass(frozen=True, slots=True)
class ModelContextCompressionSuggestion:
    suggestion_ref: str
    target_context_tokens_hint: int
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.suggestion_ref, "suggestion_ref")
        if self.target_context_tokens_hint < 0:
            raise ValueError("target_context_tokens_hint must be non-negative")


@dataclass(frozen=True, slots=True)
class ModelInvocationReplanSuggestion:
    suggestion_ref: str
    invocation_ref: str
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    suggested_next_plan_ref: str | None = None
    advisory_only: bool = True
    executes_replan: bool = False
    schema_version: str = L3_MODEL_INVOCATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.suggestion_ref, "suggestion_ref")
        _ensure_ref(self.invocation_ref, "invocation_ref")
        if not self.advisory_only or self.executes_replan:
            raise ValueError("L3 replan suggestion cannot execute a replan")
