"""L3 第四阶段 ToolIntent 编排建议对象。

本模块只表达工具意图、参数完整度、缺口与未来边界准备提示。
它不调用工具执行器，不生成真实边界审查请求，不授予工具权限。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .intent_envelope import ToolIntentEnvelope, ToolIntentParameterSpecRef, ToolIntentRef
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind


class ToolIntentAdviceKind(str, Enum):
    """工具意图建议类别。"""

    UNKNOWN = "unknown"
    ADVICE = "advice"
    MISSING_PARAMETER = "missing_parameter"
    READINESS = "readiness"
    DOWNGRADE_PATH = "downgrade_path"
    BOUNDARY_PREPARATION_HINT = "boundary_preparation_hint"
    STATE_TRANSITION = "state_transition"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class ToolIntentParameterCompletenessScore:
    """工具意图参数完整度评分；不构造真实调用参数。"""

    score_ref: TypedRef
    value: float
    expected_parameter_names: tuple[str, ...] = field(default_factory=tuple)
    provided_parameter_names: tuple[str, ...] = field(default_factory=tuple)
    missing_parameter_names: tuple[str, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.value, "ToolIntentParameterCompletenessScore.value")
        _ensure_unit_interval(self.confidence, "ToolIntentParameterCompletenessScore.confidence")
        for item in self.expected_parameter_names + self.provided_parameter_names + self.missing_parameter_names + self.reason_codes:
            _ensure_short_text(item, "ToolIntentParameterCompletenessScore short fields", 128)
        if self.advisory_only is not True:
            raise ValueError("ToolIntentParameterCompletenessScore.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolIntentParameterCompletenessScore.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolIntentReadinessScore:
    """工具意图准备度评分；只表示是否建议进入后续审查准备流程。"""

    score_ref: TypedRef
    value: float
    parameter_score_ref: TypedRef | None = None
    tool_group_release_advice_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.value, "ToolIntentReadinessScore.value")
        _ensure_unit_interval(self.confidence, "ToolIntentReadinessScore.confidence")
        for item in self.reason_codes:
            _ensure_short_text(item, "ToolIntentReadinessScore.reason_codes", 128)
        if self.advisory_only is not True:
            raise ValueError("ToolIntentReadinessScore.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolIntentReadinessScore.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolIntentAdvice:
    """工具意图总建议；不调用工具。"""

    advice_ref: TypedRef
    intent_envelope: ToolIntentEnvelope
    parameter_score: ToolIntentParameterCompletenessScore | None = None
    readiness_score: ToolIntentReadinessScore | None = None
    advice_kind: ToolIntentAdviceKind = ToolIntentAdviceKind.ADVICE
    suggested_next_step: str = "prepare_boundary_review_hint"
    reason_summary: str = ""
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_next_step, "ToolIntentAdvice.suggested_next_step", 128)
        _ensure_short_text(self.reason_summary, "ToolIntentAdvice.reason_summary")
        _ensure_unit_interval(self.confidence, "ToolIntentAdvice.confidence")
        if self.advisory_only is not True:
            raise ValueError("ToolIntentAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolIntentAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolIntentMissingParameterAdvice:
    """工具意图缺参建议；不补参，不调用模型。"""

    advice_ref: TypedRef
    intent_ref: ToolIntentRef
    missing_parameter_names: tuple[str, ...] = field(default_factory=tuple)
    parameter_spec_refs: tuple[ToolIntentParameterSpecRef, ...] = field(default_factory=tuple)
    clarification_hint: str = ""
    priority: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.missing_parameter_names:
            _ensure_short_text(item, "ToolIntentMissingParameterAdvice.missing_parameter_names", 128)
        _ensure_short_text(self.clarification_hint, "ToolIntentMissingParameterAdvice.clarification_hint")
        _ensure_unit_interval(self.priority, "ToolIntentMissingParameterAdvice.priority")
        if self.advisory_only is not True:
            raise ValueError("ToolIntentMissingParameterAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolIntentMissingParameterAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolIntentDowngradeAdvice:
    """工具意图降级建议；不执行降级。"""

    advice_ref: TypedRef
    intent_ref: ToolIntentRef
    downgrade_target_hint: str = "clarify_parameters_first"
    downgrade_score: float = 0.0
    preserved_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.downgrade_target_hint, "ToolIntentDowngradeAdvice.downgrade_target_hint", 128)
        _ensure_unit_interval(self.downgrade_score, "ToolIntentDowngradeAdvice.downgrade_score")
        _ensure_short_text(self.reason_summary, "ToolIntentDowngradeAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ToolIntentDowngradeAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolIntentDowngradeAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolIntentBoundaryPreparationHint:
    """未来边界审查准备提示；不是边界审查请求。"""

    hint_ref: TypedRef
    intent_ref: ToolIntentRef
    tool_group_ref: TypedRef | None = None
    parameter_score_ref: TypedRef | None = None
    required_review_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    preparation_reason_codes: tuple[str, ...] = field(default_factory=tuple)
    readiness_hint: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.readiness_hint, "ToolIntentBoundaryPreparationHint.readiness_hint")
        for item in self.preparation_reason_codes:
            _ensure_short_text(item, "ToolIntentBoundaryPreparationHint.preparation_reason_codes", 128)
        if self.advisory_only is not True:
            raise ValueError("ToolIntentBoundaryPreparationHint.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolIntentBoundaryPreparationHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolIntentStateTransitionAdvice:
    """工具意图状态转移建议；不写入状态。"""

    advice_ref: TypedRef
    intent_ref: ToolIntentRef
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.CREATED
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.PREPARED
    transition_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.CONTINUE_CURRENT_STEP
    transition_score: float = 0.0
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.transition_score, "ToolIntentStateTransitionAdvice.transition_score")
        _ensure_short_text(self.reason_summary, "ToolIntentStateTransitionAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ToolIntentStateTransitionAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolIntentStateTransitionAdvice.schema_version cannot be empty")


def build_tool_intent_parameter_completeness_score(
    score_ref: TypedRef,
    envelope: ToolIntentEnvelope,
) -> ToolIntentParameterCompletenessScore:
    """根据规格引用与已给参数名生成确定性完整度评分。"""

    expected = tuple(spec.parameter_name for spec in envelope.parameter_spec_refs if spec.required)
    provided = tuple(dict.fromkeys(envelope.provided_parameter_names))
    missing = tuple(name for name in expected if name not in provided)
    value = 1.0 if not expected else round((len(expected) - len(missing)) / len(expected), 6)
    return ToolIntentParameterCompletenessScore(
        score_ref=score_ref,
        value=value,
        expected_parameter_names=expected,
        provided_parameter_names=provided,
        missing_parameter_names=missing,
        reason_codes=("required parameter coverage only",),
        confidence=envelope.confidence,
    )


def build_tool_intent_readiness_score(
    score_ref: TypedRef,
    parameter_score: ToolIntentParameterCompletenessScore,
    release_readiness: float,
) -> ToolIntentReadinessScore:
    """生成工具意图准备度评分；只表示建议强度。"""

    _ensure_unit_interval(release_readiness, "build_tool_intent_readiness_score.release_readiness")
    value = round((parameter_score.value * 0.72) + (release_readiness * 0.28), 6)
    return ToolIntentReadinessScore(
        score_ref=score_ref,
        value=value,
        parameter_score_ref=parameter_score.score_ref,
        reason_codes=("parameter coverage", "tool group release readiness hint"),
        confidence=parameter_score.confidence,
    )
