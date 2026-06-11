"""L3 第四阶段 ModelIntent 编排建议对象。

本模块只表达模型意图的结构提示、澄清、拒绝、降级和状态转移建议。
它不调用模型客户端，不生成模型输出，不做自然语言意图识别算法。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .intent_envelope import ModelIntentEnvelope, ModelIntentRef
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind


class ModelIntentAdviceKind(str, Enum):
    """模型意图建议类别。"""

    UNKNOWN = "unknown"
    STRUCTURE_HINT = "structure_hint"
    ADVICE = "advice"
    AMBIGUITY = "ambiguity"
    CLARIFICATION = "clarification"
    REJECTION_PATH = "rejection_path"
    DOWNGRADE_PATH = "downgrade_path"
    STATE_TRANSITION = "state_transition"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class ModelIntentStructureHint:
    """模型意图结构提示；不调用模型补全结构。"""

    hint_ref: TypedRef
    intent_ref: ModelIntentRef
    expected_fields: tuple[str, ...] = field(default_factory=tuple)
    missing_fields: tuple[str, ...] = field(default_factory=tuple)
    conflict_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    structure_score: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.expected_fields + self.missing_fields:
            if not item or len(item) > 128:
                raise ValueError("ModelIntentStructureHint field names must be non-empty and short")
        _ensure_unit_interval(self.structure_score, "ModelIntentStructureHint.structure_score")
        _ensure_short_text(self.reason_summary, "ModelIntentStructureHint.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ModelIntentStructureHint.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ModelIntentStructureHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelIntentCompletenessScore:
    """模型意图完整度评分；只作为建议依据。"""

    score_ref: TypedRef
    value: float
    provided_fields: tuple[str, ...] = field(default_factory=tuple)
    expected_fields: tuple[str, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.value, "ModelIntentCompletenessScore.value")
        _ensure_unit_interval(self.confidence, "ModelIntentCompletenessScore.confidence")
        for item in self.reason_codes:
            _ensure_short_text(item, "ModelIntentCompletenessScore.reason_codes", 128)
        if self.advisory_only is not True:
            raise ValueError("ModelIntentCompletenessScore.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ModelIntentCompletenessScore.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelIntentAdvice:
    """模型意图总建议；只表达下一步编排倾向。"""

    advice_ref: TypedRef
    intent_envelope: ModelIntentEnvelope
    structure_hint: ModelIntentStructureHint | None = None
    completeness_score: ModelIntentCompletenessScore | None = None
    advice_kind: ModelIntentAdviceKind = ModelIntentAdviceKind.ADVICE
    suggested_next_step: str = "review_intent_structure"
    reason_summary: str = ""
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_next_step, "ModelIntentAdvice.suggested_next_step", 128)
        _ensure_short_text(self.reason_summary, "ModelIntentAdvice.reason_summary")
        _ensure_unit_interval(self.confidence, "ModelIntentAdvice.confidence")
        if self.advisory_only is not True:
            raise ValueError("ModelIntentAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ModelIntentAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelIntentAmbiguityAdvice:
    """模型意图歧义建议；不请求模型重写，只输出澄清方向。"""

    advice_ref: TypedRef
    intent_ref: ModelIntentRef
    ambiguity_score: float = 0.0
    ambiguous_fields: tuple[str, ...] = field(default_factory=tuple)
    clarification_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.ambiguity_score, "ModelIntentAmbiguityAdvice.ambiguity_score")
        for item in self.ambiguous_fields:
            _ensure_short_text(item, "ModelIntentAmbiguityAdvice.ambiguous_fields", 128)
        _ensure_short_text(self.reason_summary, "ModelIntentAmbiguityAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ModelIntentAmbiguityAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ModelIntentAmbiguityAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelIntentClarificationAdvice:
    """模型意图澄清建议；不自动发起对话。"""

    advice_ref: TypedRef
    intent_ref: ModelIntentRef
    question_hints: tuple[str, ...] = field(default_factory=tuple)
    missing_field_names: tuple[str, ...] = field(default_factory=tuple)
    clarification_priority: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.question_hints + self.missing_field_names:
            _ensure_short_text(item, "ModelIntentClarificationAdvice short fields", 256)
        _ensure_unit_interval(self.clarification_priority, "ModelIntentClarificationAdvice.clarification_priority")
        _ensure_short_text(self.reason_summary, "ModelIntentClarificationAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ModelIntentClarificationAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ModelIntentClarificationAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelIntentRejectionAdvice:
    """模型意图拒绝路径建议；不执行拒绝动作。"""

    advice_ref: TypedRef
    intent_ref: ModelIntentRef
    rejection_reason_codes: tuple[str, ...] = field(default_factory=tuple)
    alternative_path_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    rejection_score: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.rejection_reason_codes:
            _ensure_short_text(item, "ModelIntentRejectionAdvice.rejection_reason_codes", 128)
        _ensure_unit_interval(self.rejection_score, "ModelIntentRejectionAdvice.rejection_score")
        _ensure_short_text(self.reason_summary, "ModelIntentRejectionAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ModelIntentRejectionAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ModelIntentRejectionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelIntentDowngradeAdvice:
    """模型意图降级路径建议；不执行降级动作。"""

    advice_ref: TypedRef
    intent_ref: ModelIntentRef
    downgrade_target_hint: str = "clarify_before_proceeding"
    downgrade_score: float = 0.0
    preserved_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.downgrade_target_hint, "ModelIntentDowngradeAdvice.downgrade_target_hint", 128)
        _ensure_unit_interval(self.downgrade_score, "ModelIntentDowngradeAdvice.downgrade_score")
        _ensure_short_text(self.reason_summary, "ModelIntentDowngradeAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ModelIntentDowngradeAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ModelIntentDowngradeAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelIntentStateTransitionAdvice:
    """模型意图状态转移建议；不写入状态。"""

    advice_ref: TypedRef
    intent_ref: ModelIntentRef
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.CREATED
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.PREPARED
    transition_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.CONTINUE_CURRENT_STEP
    transition_score: float = 0.0
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.transition_score, "ModelIntentStateTransitionAdvice.transition_score")
        _ensure_short_text(self.reason_summary, "ModelIntentStateTransitionAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ModelIntentStateTransitionAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ModelIntentStateTransitionAdvice.schema_version cannot be empty")


def build_model_intent_completeness_score(
    score_ref: TypedRef,
    envelope: ModelIntentEnvelope,
    expected_fields: tuple[str, ...],
) -> ModelIntentCompletenessScore:
    """生成确定性模型意图完整度评分；不调用模型。"""

    expected = tuple(dict.fromkeys(expected_fields))
    provided = tuple(dict.fromkeys(envelope.provided_fields))
    if not expected:
        value = 1.0
        reason = ("no expected fields declared",)
    else:
        hit_count = sum(1 for item in expected if item in provided)
        value = round(hit_count / len(expected), 6)
        reason = ("field coverage only",)
    return ModelIntentCompletenessScore(
        score_ref=score_ref,
        value=value,
        provided_fields=provided,
        expected_fields=expected,
        reason_codes=reason,
        confidence=envelope.confidence,
    )
