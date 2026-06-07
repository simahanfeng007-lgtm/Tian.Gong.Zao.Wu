"""L3 第四阶段意图数学评分对象。

本模块只提供确定性、轻量、可解释的意图评分和数学建议。
评分结果永远是建议，不做权限裁决，不授予工具，不触发动作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .intent_envelope import ActionIntentEnvelope, ModelIntentEnvelope, ToolIntentEnvelope
from .orchestration_continuity import ContinuityEvaluationSet
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_math import MathConstraintSet, MathObjectiveVector, MathScoreVector, ScoreDirection
from .orchestration_math_input import AffectiveWeightInput, DynamicDriveInput
from .orchestration_math_result import RecommendationMode
from .skill_tool_math import SkillToolMathResult


class IntentScoreKind(str, Enum):
    """意图评分类别。"""

    COMPLETENESS = "completeness"
    COHERENCE = "coherence"
    AMBIGUITY = "ambiguity"
    READINESS = "readiness"
    CONTINUITY = "continuity"
    REVERSIBILITY = "reversibility"
    DEGRADE = "degrade"
    CLARIFICATION_NEED = "clarification_need"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class IntentScoreBase:
    """意图评分基类；只表达建议事实。"""

    score_ref: TypedRef
    score_kind: IntentScoreKind
    value: float = 0.0
    confidence: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.value, f"{self.__class__.__name__}.value")
        _ensure_unit_interval(self.confidence, f"{self.__class__.__name__}.confidence")
        for item in self.reason_codes:
            _ensure_short_text(item, f"{self.__class__.__name__}.reason_codes", 128)
        if self.advisory_only is not True:
            raise ValueError(f"{self.__class__.__name__}.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentCompletenessScore(IntentScoreBase):
    score_kind: IntentScoreKind = IntentScoreKind.COMPLETENESS


@dataclass(frozen=True, slots=True)
class IntentCoherenceScore(IntentScoreBase):
    score_kind: IntentScoreKind = IntentScoreKind.COHERENCE


@dataclass(frozen=True, slots=True)
class IntentAmbiguityScore(IntentScoreBase):
    score_kind: IntentScoreKind = IntentScoreKind.AMBIGUITY


@dataclass(frozen=True, slots=True)
class IntentReadinessScore(IntentScoreBase):
    score_kind: IntentScoreKind = IntentScoreKind.READINESS


@dataclass(frozen=True, slots=True)
class IntentContinuityScore(IntentScoreBase):
    score_kind: IntentScoreKind = IntentScoreKind.CONTINUITY


@dataclass(frozen=True, slots=True)
class IntentReversibilityScore(IntentScoreBase):
    score_kind: IntentScoreKind = IntentScoreKind.REVERSIBILITY


@dataclass(frozen=True, slots=True)
class IntentDegradeScore(IntentScoreBase):
    score_kind: IntentScoreKind = IntentScoreKind.DEGRADE


@dataclass(frozen=True, slots=True)
class IntentClarificationNeedScore(IntentScoreBase):
    score_kind: IntentScoreKind = IntentScoreKind.CLARIFICATION_NEED


@dataclass(frozen=True, slots=True)
class IntentMathInput:
    """意图数学输入；仅引用状态、上下文和候选，不运行策略。"""

    input_ref: TypedRef
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    model_intent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    tool_intent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    action_intent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    objective_vector: MathObjectiveVector | None = None
    constraint_set: MathConstraintSet | None = None
    continuity_evaluation: ContinuityEvaluationSet | None = None
    skill_tool_math_result: SkillToolMathResult | None = None
    affective_input: AffectiveWeightInput | None = None
    dynamic_drive_input: DynamicDriveInput | None = None
    stability_constraint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reversibility_constraint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "IntentMathInput.summary")
        if self.advisory_only is not True:
            raise ValueError("IntentMathInput.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentMathInput.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentMathResult:
    """意图数学评分结果；不代表最终动作。"""

    result_ref: TypedRef
    math_input: IntentMathInput
    score_vector: MathScoreVector
    intent_route_ranking_ref: TypedRef | None = None
    validation_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "IntentMathResult.confidence")
        _ensure_short_text(self.reason_summary, "IntentMathResult.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentMathResult.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentMathResult.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentRecommendation:
    """意图推荐；只表达建议路径。"""

    recommendation_ref: TypedRef
    math_result: IntentMathResult
    recommendation_mode: RecommendationMode = RecommendationMode.SUGGEST
    recommended_intent_ref: TypedRef | None = None
    recommended_route_ref: TypedRef | None = None
    clarification_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    downgrade_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_preparation_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.recommendation_mode is not RecommendationMode.SUGGEST:
            raise ValueError("IntentRecommendation.recommendation_mode must remain SUGGEST")
        _ensure_unit_interval(self.confidence, "IntentRecommendation.confidence")
        _ensure_short_text(self.reason_summary, "IntentRecommendation.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentRecommendation.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentRecommendation.schema_version cannot be empty")


def _coverage_score(provided: tuple[str, ...], expected: tuple[str, ...]) -> float:
    if not expected:
        return 1.0
    return round(sum(1 for item in expected if item in provided) / len(expected), 6)


def build_intent_completeness_score(
    score_ref: TypedRef,
    provided_fields: tuple[str, ...],
    expected_fields: tuple[str, ...],
    confidence: float = 0.8,
) -> IntentCompletenessScore:
    """根据字段名覆盖率生成完整度评分。"""

    value = _coverage_score(tuple(dict.fromkeys(provided_fields)), tuple(dict.fromkeys(expected_fields)))
    return IntentCompletenessScore(
        score_ref=score_ref,
        value=value,
        confidence=confidence,
        reason_codes=("field coverage only",),
    )


def build_intent_ambiguity_score(score_ref: TypedRef, ambiguity_count: int, field_count: int, confidence: float = 0.8) -> IntentAmbiguityScore:
    """根据歧义字段数量生成歧义评分。"""

    denominator = max(field_count, 1)
    value = round(min(max(ambiguity_count, 0) / denominator, 1.0), 6)
    return IntentAmbiguityScore(
        score_ref=score_ref,
        value=value,
        confidence=confidence,
        reason_codes=("ambiguous field ratio",),
    )


def build_intent_readiness_score(
    score_ref: TypedRef,
    completeness: IntentCompletenessScore,
    ambiguity: IntentAmbiguityScore,
    continuity: float = 0.0,
    reversibility: float = 0.0,
) -> IntentReadinessScore:
    """生成意图准备度评分；不表达执行许可。"""

    _ensure_unit_interval(continuity, "build_intent_readiness_score.continuity")
    _ensure_unit_interval(reversibility, "build_intent_readiness_score.reversibility")
    value = round(
        (completeness.value * 0.42)
        + ((1.0 - ambiguity.value) * 0.26)
        + (continuity * 0.18)
        + (reversibility * 0.14),
        6,
    )
    return IntentReadinessScore(
        score_ref=score_ref,
        value=value,
        confidence=min(completeness.confidence, ambiguity.confidence),
        reason_codes=("completeness", "ambiguity_inverse", "continuity", "reversibility"),
    )


def build_intent_degrade_score(score_ref: TypedRef, ambiguity: IntentAmbiguityScore, completeness: IntentCompletenessScore) -> IntentDegradeScore:
    """生成降级建议强度评分。"""

    value = round((ambiguity.value * 0.58) + ((1.0 - completeness.value) * 0.42), 6)
    return IntentDegradeScore(
        score_ref=score_ref,
        value=value,
        confidence=min(ambiguity.confidence, completeness.confidence),
        reason_codes=("ambiguity", "missing_fields"),
    )


def build_intent_clarification_need_score(
    score_ref: TypedRef,
    ambiguity: IntentAmbiguityScore,
    completeness: IntentCompletenessScore,
    affective_input: AffectiveWeightInput | None = None,
    dynamic_drive_input: DynamicDriveInput | None = None,
) -> IntentClarificationNeedScore:
    """生成澄清需要评分；情感/动态驱动只调节倾向。"""

    caution = affective_input.caution_weight if affective_input is not None else 0.0
    risk_pressure = dynamic_drive_input.risk_pressure_weight if dynamic_drive_input is not None else 0.0
    value = round(
        min(
            1.0,
            (ambiguity.value * 0.44)
            + ((1.0 - completeness.value) * 0.34)
            + (caution * 0.12)
            + (risk_pressure * 0.10),
        ),
        6,
    )
    return IntentClarificationNeedScore(
        score_ref=score_ref,
        value=value,
        confidence=min(ambiguity.confidence, completeness.confidence),
        reason_codes=("ambiguity", "missing_fields", "caution_tendency", "risk_pressure_tendency"),
    )


def build_intent_score_vector(score_ref: TypedRef, scores: tuple[IntentScoreBase, ...]) -> MathScoreVector:
    """把第四阶段意图评分映射到第一阶段 MathScoreVector。"""

    benefit_kinds = {IntentScoreKind.COMPLETENESS, IntentScoreKind.COHERENCE, IntentScoreKind.READINESS, IntentScoreKind.CONTINUITY, IntentScoreKind.REVERSIBILITY}
    entries = tuple(
        (
            score.score_kind.value,
            score.value,
            ScoreDirection.BENEFIT if score.score_kind in benefit_kinds else ScoreDirection.COST,
        )
        for score in scores
    )
    normalized_score = round(sum(item[1] for item in entries) / len(entries), 6) if entries else 0.0
    penalty_total = round(sum(item[1] for item in entries if item[2] is ScoreDirection.COST), 6)
    bonus_total = round(sum(item[1] for item in entries if item[2] is ScoreDirection.BENEFIT), 6)
    return MathScoreVector(
        score_ref=score_ref,
        score_entries=entries,
        source_score_refs=tuple(score.score_ref for score in scores),
        normalized_score=normalized_score,
        confidence=min((score.confidence for score in scores), default=0.0),
        penalty_total=penalty_total,
        bonus_total=bonus_total,
        summary="intent orchestration score vector",
    )


def score_model_envelope_completeness(score_ref: TypedRef, envelope: ModelIntentEnvelope) -> IntentCompletenessScore:
    """从模型意图信封生成通用完整度评分。"""

    expected = envelope.provided_fields + envelope.missing_fields
    return build_intent_completeness_score(score_ref, envelope.provided_fields, expected, envelope.confidence)


def score_tool_envelope_completeness(score_ref: TypedRef, envelope: ToolIntentEnvelope) -> IntentCompletenessScore:
    """从工具意图信封生成通用完整度评分。"""

    expected = envelope.provided_parameter_names + envelope.missing_parameter_names
    return build_intent_completeness_score(score_ref, envelope.provided_parameter_names, expected, envelope.confidence)


def score_action_envelope_completeness(score_ref: TypedRef, envelope: ActionIntentEnvelope) -> IntentCompletenessScore:
    """从动作意图信封生成通用完整度评分。"""

    expected = envelope.provided_fields + envelope.missing_fields
    return build_intent_completeness_score(score_ref, envelope.provided_fields, expected, envelope.confidence)
