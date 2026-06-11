"""L3 第五阶段边界/执行请求数学评分对象。

评分只用于请求准备度、证据充分性、前置条件完整度与路径排序建议。
它不做权限裁决、不做风险放行、不签发确认、不授予租约、不触发执行。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .boundary_request import BoundaryCheckEnvelope, BoundaryCheckRequest
from .boundary_route_advice import BoundaryRouteRanking
from .execution_request import ExecutionDispatchRequest, ExecutionPreconditionHint, ExecutionRequest
from .execution_routing_advice import ExecutionRouteRanking
from .intent_math import IntentMathResult
from .orchestration_continuity import ContinuityEvaluationSet
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_math import MathConstraintSet, MathObjectiveVector, MathScoreVector, ScoreDirection
from .orchestration_math_input import AffectiveWeightInput, DynamicDriveInput
from .orchestration_math_result import RecommendationMode
from .skill_tool_math import SkillToolMathResult


class BoundaryExecutionScoreKind(str, Enum):
    """边界/执行评分类别。"""

    BOUNDARY_READINESS = "boundary_readiness"
    BOUNDARY_COMPLETENESS = "boundary_completeness"
    BOUNDARY_EVIDENCE_SUFFICIENCY = "boundary_evidence_sufficiency"
    BOUNDARY_CLARIFICATION_NEED = "boundary_clarification_need"
    EXECUTION_READINESS = "execution_readiness"
    EXECUTION_PRECONDITION_COMPLETENESS = "execution_precondition_completeness"
    EXECUTION_CONTINUITY = "execution_continuity"
    EXECUTION_REVERSIBILITY = "execution_reversibility"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_advisory(flag: bool, field_name: str) -> None:
    if flag is not True:
        raise ValueError(f"{field_name} must remain true")


@dataclass(frozen=True, slots=True)
class BoundaryExecutionScoreBase:
    """边界/执行评分基类；只表达建议事实。"""

    score_ref: TypedRef
    score_kind: BoundaryExecutionScoreKind
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
        _ensure_advisory(self.advisory_only, f"{self.__class__.__name__}.advisory_only")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryReadinessScore(BoundaryExecutionScoreBase):
    score_kind: BoundaryExecutionScoreKind = BoundaryExecutionScoreKind.BOUNDARY_READINESS


@dataclass(frozen=True, slots=True)
class BoundaryCompletenessScore(BoundaryExecutionScoreBase):
    score_kind: BoundaryExecutionScoreKind = BoundaryExecutionScoreKind.BOUNDARY_COMPLETENESS


@dataclass(frozen=True, slots=True)
class BoundaryEvidenceSufficiencyScore(BoundaryExecutionScoreBase):
    score_kind: BoundaryExecutionScoreKind = BoundaryExecutionScoreKind.BOUNDARY_EVIDENCE_SUFFICIENCY


@dataclass(frozen=True, slots=True)
class BoundaryClarificationNeedScore(BoundaryExecutionScoreBase):
    score_kind: BoundaryExecutionScoreKind = BoundaryExecutionScoreKind.BOUNDARY_CLARIFICATION_NEED


@dataclass(frozen=True, slots=True)
class ExecutionReadinessScore(BoundaryExecutionScoreBase):
    score_kind: BoundaryExecutionScoreKind = BoundaryExecutionScoreKind.EXECUTION_READINESS


@dataclass(frozen=True, slots=True)
class ExecutionPreconditionCompletenessScore(BoundaryExecutionScoreBase):
    score_kind: BoundaryExecutionScoreKind = BoundaryExecutionScoreKind.EXECUTION_PRECONDITION_COMPLETENESS


@dataclass(frozen=True, slots=True)
class ExecutionContinuityScore(BoundaryExecutionScoreBase):
    score_kind: BoundaryExecutionScoreKind = BoundaryExecutionScoreKind.EXECUTION_CONTINUITY


@dataclass(frozen=True, slots=True)
class ExecutionReversibilityScore(BoundaryExecutionScoreBase):
    score_kind: BoundaryExecutionScoreKind = BoundaryExecutionScoreKind.EXECUTION_REVERSIBILITY


@dataclass(frozen=True, slots=True)
class BoundaryExecutionMathInput:
    """边界/执行数学输入；只引用前置编排对象。"""

    input_ref: TypedRef
    boundary_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    execution_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    intent_math_result: IntentMathResult | None = None
    skill_tool_math_result: SkillToolMathResult | None = None
    continuity_evaluation: ContinuityEvaluationSet | None = None
    objective_vector: MathObjectiveVector | None = None
    constraint_set: MathConstraintSet | None = None
    affective_input: AffectiveWeightInput | None = None
    dynamic_drive_input: DynamicDriveInput | None = None
    future_l5_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_l4_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "BoundaryExecutionMathInput.summary")
        _ensure_advisory(self.advisory_only, "BoundaryExecutionMathInput.advisory_only")
        if not self.schema_version:
            raise ValueError("BoundaryExecutionMathInput.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryExecutionMathResult:
    """边界/执行数学结果；不代表审查或执行结果。"""

    result_ref: TypedRef
    math_input: BoundaryExecutionMathInput
    score_vector: MathScoreVector
    boundary_route_ranking_ref: TypedRef | None = None
    execution_route_ranking_ref: TypedRef | None = None
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "BoundaryExecutionMathResult.confidence")
        _ensure_short_text(self.reason_summary, "BoundaryExecutionMathResult.reason_summary")
        _ensure_advisory(self.advisory_only, "BoundaryExecutionMathResult.advisory_only")
        if not self.schema_version:
            raise ValueError("BoundaryExecutionMathResult.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryExecutionRecommendation:
    """边界/执行推荐；只输出建议路径。"""

    recommendation_ref: TypedRef
    math_result: BoundaryExecutionMathResult
    recommendation_mode: RecommendationMode = RecommendationMode.SUGGEST
    recommended_boundary_route_ref: TypedRef | None = None
    recommended_execution_route_ref: TypedRef | None = None
    boundary_review_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    execution_preparation_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.recommendation_mode is not RecommendationMode.SUGGEST:
            raise ValueError("BoundaryExecutionRecommendation.recommendation_mode must remain SUGGEST")
        _ensure_unit_interval(self.confidence, "BoundaryExecutionRecommendation.confidence")
        _ensure_short_text(self.reason_summary, "BoundaryExecutionRecommendation.reason_summary")
        _ensure_advisory(self.advisory_only, "BoundaryExecutionRecommendation.advisory_only")
        if not self.schema_version:
            raise ValueError("BoundaryExecutionRecommendation.schema_version cannot be empty")


def _coverage_score(present: tuple[str, ...], missing: tuple[str, ...]) -> float:
    total = len(tuple(dict.fromkeys(present + missing)))
    if total == 0:
        return 1.0
    return round(len(tuple(dict.fromkeys(present))) / total, 6)


def build_boundary_completeness_score(score_ref: TypedRef, envelope: BoundaryCheckEnvelope, confidence: float = 0.82) -> BoundaryCompletenessScore:
    """根据边界请求信封字段覆盖率生成完整度评分。"""

    return BoundaryCompletenessScore(
        score_ref=score_ref,
        value=_coverage_score(envelope.present_field_names, envelope.missing_field_names),
        confidence=confidence,
        reason_codes=("boundary request field coverage only",),
    )


def build_boundary_evidence_sufficiency_score(
    score_ref: TypedRef,
    request: BoundaryCheckRequest,
    expected_evidence_count: int = 1,
    confidence: float = 0.78,
) -> BoundaryEvidenceSufficiencyScore:
    """根据证据引用数量生成证据充分性评分；不读取证据。"""

    denominator = max(expected_evidence_count, 1)
    value = round(min(len(request.evidence_refs) / denominator, 1.0), 6)
    return BoundaryEvidenceSufficiencyScore(
        score_ref=score_ref,
        value=value,
        confidence=confidence,
        reason_codes=("evidence reference count only",),
        evidence_refs=tuple(item.evidence_ref for item in request.evidence_refs),
    )


def build_boundary_clarification_need_score(
    score_ref: TypedRef,
    completeness: BoundaryCompletenessScore,
    evidence: BoundaryEvidenceSufficiencyScore,
    affective_input: AffectiveWeightInput | None = None,
    dynamic_drive_input: DynamicDriveInput | None = None,
) -> BoundaryClarificationNeedScore:
    """生成澄清需要评分；情感/动态只改变倾向。"""

    base = (1.0 - completeness.value) * 0.62 + (1.0 - evidence.value) * 0.28
    if affective_input is not None:
        base += affective_input.caution_weight * 0.06
    if dynamic_drive_input is not None:
        base += dynamic_drive_input.risk_pressure_weight * 0.04
    return BoundaryClarificationNeedScore(
        score_ref=score_ref,
        value=round(min(max(base, 0.0), 1.0), 6),
        confidence=min(completeness.confidence, evidence.confidence),
        reason_codes=("missing boundary fields and evidence only",),
    )


def build_boundary_readiness_score(
    score_ref: TypedRef,
    completeness: BoundaryCompletenessScore,
    evidence: BoundaryEvidenceSufficiencyScore,
    clarification_need: BoundaryClarificationNeedScore,
) -> BoundaryReadinessScore:
    """生成边界请求准备度评分；不表达审查通过。"""

    value = completeness.value * 0.45 + evidence.value * 0.35 + (1.0 - clarification_need.value) * 0.20
    return BoundaryReadinessScore(
        score_ref=score_ref,
        value=round(min(max(value, 0.0), 1.0), 6),
        confidence=min(completeness.confidence, evidence.confidence, clarification_need.confidence),
        reason_codes=("request readiness only not review outcome",),
    )


def build_execution_precondition_completeness_score(
    score_ref: TypedRef,
    precondition_hint: ExecutionPreconditionHint,
    confidence: float = 0.8,
) -> ExecutionPreconditionCompletenessScore:
    """根据前置条件引用覆盖率生成评分；不检查真实环境。"""

    return ExecutionPreconditionCompletenessScore(
        score_ref=score_ref,
        value=precondition_hint.precondition_score,
        confidence=confidence,
        reason_codes=("precondition reference coverage only",),
        evidence_refs=precondition_hint.satisfied_precondition_refs,
    )


def build_execution_readiness_score(
    score_ref: TypedRef,
    execution_request: ExecutionRequest,
    precondition_score: ExecutionPreconditionCompletenessScore,
    boundary_readiness: BoundaryReadinessScore,
    continuity_score: float = 0.0,
    reversibility_score: float = 0.0,
) -> ExecutionReadinessScore:
    """生成未来 L4 请求准备度评分；不授权执行。"""

    _ensure_unit_interval(continuity_score, "build_execution_readiness_score.continuity_score")
    _ensure_unit_interval(reversibility_score, "build_execution_readiness_score.reversibility_score")
    field_score = _coverage_score(execution_request.payload_field_names, execution_request.missing_field_names)
    value = (
        field_score * 0.24
        + precondition_score.value * 0.25
        + boundary_readiness.value * 0.21
        + continuity_score * 0.18
        + reversibility_score * 0.12
    )
    return ExecutionReadinessScore(
        score_ref=score_ref,
        value=round(min(max(value, 0.0), 1.0), 6),
        confidence=min(precondition_score.confidence, boundary_readiness.confidence),
        reason_codes=("execution request readiness only not authorization",),
    )


def build_boundary_execution_score_vector(score_ref: TypedRef, scores: tuple[BoundaryExecutionScoreBase, ...]) -> MathScoreVector:
    """把边界/执行评分映射到第一阶段 MathScoreVector。"""

    score_entries: list[tuple[TypedRef, float, ScoreDirection, str]] = []
    for score in scores:
        direction = ScoreDirection.COST if score.score_kind is BoundaryExecutionScoreKind.BOUNDARY_CLARIFICATION_NEED else ScoreDirection.BENEFIT
        score_entries.append((score.score_kind.value, score.value, direction))
    return MathScoreVector(
        score_ref=score_ref,
        score_entries=tuple(score_entries),
        source_score_refs=tuple(score.score_ref for score in scores),
        normalized_score=round(sum(score.value for score in scores) / len(scores), 6) if scores else 0.0,
        confidence=min((score.confidence for score in scores), default=0.0),
        penalty_total=round(sum(score.value for score in scores if score.score_kind is BoundaryExecutionScoreKind.BOUNDARY_CLARIFICATION_NEED), 6),
        bonus_total=round(sum(score.value for score in scores if score.score_kind is not BoundaryExecutionScoreKind.BOUNDARY_CLARIFICATION_NEED), 6),
        summary="boundary/execution request scoring advice only",
    )
