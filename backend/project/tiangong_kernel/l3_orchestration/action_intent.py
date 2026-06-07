"""L3 第四阶段 ActionIntent 编排建议对象。

本模块只表达动作意图、前置条件、可逆性提示与准备度建议。
它不执行动作，不调用工具，不写文件，不发网络请求，不执行 shell。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .intent_envelope import ActionIntentEnvelope, ActionIntentRef, ActionIntentTargetRef
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind


class ActionIntentAdviceKind(str, Enum):
    """动作意图建议类别。"""

    UNKNOWN = "unknown"
    ADVICE = "advice"
    PRECONDITION_HINT = "precondition_hint"
    READINESS = "readiness"
    REVERSIBILITY = "reversibility"
    DOWNGRADE_PATH = "downgrade_path"
    STATE_TRANSITION = "state_transition"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class ActionIntentPreconditionHint:
    """动作意图前置条件提示；不检查真实外部状态。"""

    hint_ref: TypedRef
    intent_ref: ActionIntentRef
    required_precondition_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    satisfied_precondition_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_precondition_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    precondition_score: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.precondition_score, "ActionIntentPreconditionHint.precondition_score")
        _ensure_short_text(self.reason_summary, "ActionIntentPreconditionHint.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ActionIntentPreconditionHint.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ActionIntentPreconditionHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ActionIntentCompletenessScore:
    """动作意图完整度评分；只作为建议依据。"""

    score_ref: TypedRef
    value: float
    provided_fields: tuple[str, ...] = field(default_factory=tuple)
    expected_fields: tuple[str, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.value, "ActionIntentCompletenessScore.value")
        _ensure_unit_interval(self.confidence, "ActionIntentCompletenessScore.confidence")
        for item in self.reason_codes:
            _ensure_short_text(item, "ActionIntentCompletenessScore.reason_codes", 128)
        if self.advisory_only is not True:
            raise ValueError("ActionIntentCompletenessScore.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ActionIntentCompletenessScore.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ActionIntentReadinessScore:
    """动作意图准备度评分；不等于执行授权。"""

    score_ref: TypedRef
    value: float
    completeness_score_ref: TypedRef | None = None
    precondition_hint_ref: TypedRef | None = None
    reversibility_hint_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.value, "ActionIntentReadinessScore.value")
        _ensure_unit_interval(self.confidence, "ActionIntentReadinessScore.confidence")
        for item in self.reason_codes:
            _ensure_short_text(item, "ActionIntentReadinessScore.reason_codes", 128)
        if self.advisory_only is not True:
            raise ValueError("ActionIntentReadinessScore.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ActionIntentReadinessScore.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ActionIntentReversibilityHint:
    """动作意图可逆性提示；不执行回滚或恢复。"""

    hint_ref: TypedRef
    intent_ref: ActionIntentRef
    reversibility_score: float = 0.0
    reversible_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    irreversible_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.reversibility_score, "ActionIntentReversibilityHint.reversibility_score")
        _ensure_short_text(self.reason_summary, "ActionIntentReversibilityHint.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ActionIntentReversibilityHint.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ActionIntentReversibilityHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ActionIntentAdvice:
    """动作意图总建议；不执行动作。"""

    advice_ref: TypedRef
    intent_envelope: ActionIntentEnvelope
    precondition_hint: ActionIntentPreconditionHint | None = None
    readiness_score: ActionIntentReadinessScore | None = None
    target_refs: tuple[ActionIntentTargetRef, ...] = field(default_factory=tuple)
    advice_kind: ActionIntentAdviceKind = ActionIntentAdviceKind.ADVICE
    suggested_next_step: str = "prepare_action_review_hint"
    reason_summary: str = ""
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_next_step, "ActionIntentAdvice.suggested_next_step", 128)
        _ensure_short_text(self.reason_summary, "ActionIntentAdvice.reason_summary")
        _ensure_unit_interval(self.confidence, "ActionIntentAdvice.confidence")
        if self.advisory_only is not True:
            raise ValueError("ActionIntentAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ActionIntentAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ActionIntentDowngradeAdvice:
    """动作意图降级建议；不执行降级。"""

    advice_ref: TypedRef
    intent_ref: ActionIntentRef
    downgrade_target_hint: str = "clarify_action_preconditions_first"
    downgrade_score: float = 0.0
    preserved_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.downgrade_target_hint, "ActionIntentDowngradeAdvice.downgrade_target_hint", 128)
        _ensure_unit_interval(self.downgrade_score, "ActionIntentDowngradeAdvice.downgrade_score")
        _ensure_short_text(self.reason_summary, "ActionIntentDowngradeAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ActionIntentDowngradeAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ActionIntentDowngradeAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ActionIntentStateTransitionAdvice:
    """动作意图状态转移建议；不写入状态。"""

    advice_ref: TypedRef
    intent_ref: ActionIntentRef
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.CREATED
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.PREPARED
    transition_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.CONTINUE_CURRENT_STEP
    transition_score: float = 0.0
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.transition_score, "ActionIntentStateTransitionAdvice.transition_score")
        _ensure_short_text(self.reason_summary, "ActionIntentStateTransitionAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ActionIntentStateTransitionAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ActionIntentStateTransitionAdvice.schema_version cannot be empty")


def build_action_intent_completeness_score(
    score_ref: TypedRef,
    envelope: ActionIntentEnvelope,
    expected_fields: tuple[str, ...],
) -> ActionIntentCompletenessScore:
    """生成动作意图完整度评分；只比较字段名。"""

    expected = tuple(dict.fromkeys(expected_fields))
    provided = tuple(dict.fromkeys(envelope.provided_fields))
    value = 1.0 if not expected else round(sum(1 for item in expected if item in provided) / len(expected), 6)
    return ActionIntentCompletenessScore(
        score_ref=score_ref,
        value=value,
        provided_fields=provided,
        expected_fields=expected,
        reason_codes=("action field coverage only",),
        confidence=envelope.confidence,
    )


def build_action_intent_readiness_score(
    score_ref: TypedRef,
    completeness_score: ActionIntentCompletenessScore,
    precondition_hint: ActionIntentPreconditionHint,
    reversibility_hint: ActionIntentReversibilityHint,
) -> ActionIntentReadinessScore:
    """生成动作意图准备度评分；只作为建议。"""

    value = round(
        (completeness_score.value * 0.46)
        + (precondition_hint.precondition_score * 0.34)
        + (reversibility_hint.reversibility_score * 0.20),
        6,
    )
    return ActionIntentReadinessScore(
        score_ref=score_ref,
        value=value,
        completeness_score_ref=completeness_score.score_ref,
        precondition_hint_ref=precondition_hint.hint_ref,
        reversibility_hint_ref=reversibility_hint.hint_ref,
        reason_codes=("completeness", "precondition", "reversibility"),
        confidence=completeness_score.confidence,
    )
