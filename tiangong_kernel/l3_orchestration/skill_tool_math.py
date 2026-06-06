"""L3 第三阶段 Skill / ToolGroup 数学评分输入、结果与建议对象。

本模块只做轻量、确定性、可解释的编排评分建议。
评分不得替代权限裁决，不得授予工具，不得触发真实动作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_continuity import ContinuityEvaluationSet
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_math import MathConstraintSet, MathObjectiveVector, MathScoreVector, ScoreDirection
from .orchestration_math_input import AffectiveWeightInput, DynamicDriveInput
from .orchestration_math_result import MathEvaluation, MathRecommendation, RecommendationMode
from .skill_visibility import SkillDisplayCandidate, SkillSelectionAdvice
from .tool_group_release_advice import ToolGroupReleaseAdvice, ToolGroupReleaseCandidate, ToolGroupReleaseRanking


class SkillToolScoreKind(str, Enum):
    """Skill / ToolGroup 编排评分种类。"""

    UNKNOWN = "unknown"
    SKILL_MATCH = "skill_match"
    SKILL_RELEVANCE = "skill_relevance"
    SKILL_CONTINUITY = "skill_continuity"
    SKILL_READINESS = "skill_readiness"
    SKILL_RISK_AWARENESS = "skill_risk_awareness"
    TOOL_GROUP_NEED = "tool_group_need"
    TOOL_GROUP_MINIMALITY = "tool_group_minimality"
    TOOL_EXPOSURE_COST = "tool_exposure_cost"
    TOOL_GROUP_EXPOSURE_COST = "tool_group_exposure_cost"
    TOOL_GROUP_READINESS = "tool_group_readiness"
    TOOL_GROUP_COMPLETENESS = "tool_group_completeness"
    TOOL_GROUP_SUFFICIENCY = "tool_group_sufficiency"
    REVERSIBILITY_INDEX = "reversibility_index"
    STABILITY_INDEX = "stability_index"


def _unit(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


@dataclass(frozen=True, slots=True)
class SkillToolScoreBase:
    """Skill / ToolGroup 编排评分基础对象。"""

    score_ref: TypedRef | None = None
    score_kind: SkillToolScoreKind = SkillToolScoreKind.UNKNOWN
    value: float = 0.0
    confidence: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.value, f"{type(self).__name__}.value")
        _ensure_unit_interval(self.confidence, f"{type(self).__name__}.confidence")
        if any(len(item) > 128 for item in self.reason_codes):
            raise ValueError(f"{type(self).__name__}.reason_codes entries must be short")
        if self.advisory_only is not True:
            raise ValueError(f"{type(self).__name__}.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError(f"{type(self).__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillMatchScore(SkillToolScoreBase):
    """Skill 与任务目标匹配度。"""

    score_kind: SkillToolScoreKind = SkillToolScoreKind.SKILL_MATCH


@dataclass(frozen=True, slots=True)
class SkillRelevanceScore(SkillToolScoreBase):
    """Skill 与当前上下文相关度。"""

    score_kind: SkillToolScoreKind = SkillToolScoreKind.SKILL_RELEVANCE


@dataclass(frozen=True, slots=True)
class SkillContinuityScore(SkillToolScoreBase):
    """Skill 与 Run / Task / Turn / Step 连续性的贴合度。"""

    score_kind: SkillToolScoreKind = SkillToolScoreKind.SKILL_CONTINUITY


@dataclass(frozen=True, slots=True)
class SkillReadinessScore(SkillToolScoreBase):
    """Skill 进入后续编排流程的准备度。"""

    score_kind: SkillToolScoreKind = SkillToolScoreKind.SKILL_READINESS


@dataclass(frozen=True, slots=True)
class SkillRiskAwarenessHint(SkillToolScoreBase):
    """Skill 相关风险提示强度；仅用于提示后续边界审查。"""

    score_kind: SkillToolScoreKind = SkillToolScoreKind.SKILL_RISK_AWARENESS


@dataclass(frozen=True, slots=True)
class ToolGroupNeedScore(SkillToolScoreBase):
    """工具组需求强度。"""

    score_kind: SkillToolScoreKind = SkillToolScoreKind.TOOL_GROUP_NEED


@dataclass(frozen=True, slots=True)
class ToolGroupMinimalityScore(SkillToolScoreBase):
    """工具组最小充分程度。"""

    score_kind: SkillToolScoreKind = SkillToolScoreKind.TOOL_GROUP_MINIMALITY


@dataclass(frozen=True, slots=True)
class ToolExposureCostScore(SkillToolScoreBase):
    """工具暴露成本。"""

    score_kind: SkillToolScoreKind = SkillToolScoreKind.TOOL_EXPOSURE_COST


@dataclass(frozen=True, slots=True)
class ToolGroupExposureCostScore(SkillToolScoreBase):
    """工具组暴露成本。"""

    score_kind: SkillToolScoreKind = SkillToolScoreKind.TOOL_GROUP_EXPOSURE_COST


@dataclass(frozen=True, slots=True)
class ToolGroupReadinessScore(SkillToolScoreBase):
    """工具组进入后续流程的准备度。"""

    score_kind: SkillToolScoreKind = SkillToolScoreKind.TOOL_GROUP_READINESS


@dataclass(frozen=True, slots=True)
class ToolGroupCompletenessScore(SkillToolScoreBase):
    """工具组完整性评分。"""

    score_kind: SkillToolScoreKind = SkillToolScoreKind.TOOL_GROUP_COMPLETENESS


@dataclass(frozen=True, slots=True)
class ToolGroupSufficiencyScore(SkillToolScoreBase):
    """工具组是否足够支撑后续意图。"""

    score_kind: SkillToolScoreKind = SkillToolScoreKind.TOOL_GROUP_SUFFICIENCY


@dataclass(frozen=True, slots=True)
class ReversibilityIndex(SkillToolScoreBase):
    """后续路径可逆性指数。"""

    score_kind: SkillToolScoreKind = SkillToolScoreKind.REVERSIBILITY_INDEX


@dataclass(frozen=True, slots=True)
class StabilityIndex(SkillToolScoreBase):
    """流程稳定性指数。"""

    score_kind: SkillToolScoreKind = SkillToolScoreKind.STABILITY_INDEX


@dataclass(frozen=True, slots=True)
class SkillToolMathInput:
    """Skill / ToolGroup 编排评分输入。"""

    input_ref: TypedRef
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    skill_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    tool_group_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    objective_vector: MathObjectiveVector | None = None
    constraint_set: MathConstraintSet | None = None
    continuity_evaluation: ContinuityEvaluationSet | None = None
    affective_input: AffectiveWeightInput | None = None
    dynamic_drive_input: DynamicDriveInput | None = None
    stability_constraint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reversibility_constraint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "SkillToolMathInput.summary")
        if self.advisory_only is not True:
            raise ValueError("SkillToolMathInput.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillToolMathInput.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillToolMathResult:
    """Skill / ToolGroup 编排评分结果。"""

    result_ref: TypedRef
    math_input: SkillToolMathInput
    score_vector: MathScoreVector
    skill_route_ranking_ref: TypedRef | None = None
    tool_group_release_ranking: ToolGroupReleaseRanking | None = None
    evaluation: MathEvaluation | None = None
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "SkillToolMathResult.confidence")
        _ensure_short_text(self.reason_summary, "SkillToolMathResult.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("SkillToolMathResult.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillToolMathResult.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillToolRecommendation:
    """Skill / ToolGroup 编排建议总结果。"""

    recommendation_ref: TypedRef
    math_result: SkillToolMathResult
    skill_selection_advice: SkillSelectionAdvice | None = None
    tool_group_release_advice: ToolGroupReleaseAdvice | None = None
    math_recommendation: MathRecommendation | None = None
    recommendation_mode: RecommendationMode = RecommendationMode.SUGGEST
    state_transition_suggestion_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "SkillToolRecommendation.confidence")
        _ensure_short_text(self.reason_summary, "SkillToolRecommendation.reason_summary")
        if self.recommendation_mode is not RecommendationMode.SUGGEST:
            raise ValueError("SkillToolRecommendation.recommendation_mode must remain SUGGEST")
        if self.advisory_only is not True:
            raise ValueError("SkillToolRecommendation.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillToolRecommendation.schema_version cannot be empty")


def build_skill_match_score(candidate: SkillDisplayCandidate, score_ref: TypedRef | None = None) -> SkillMatchScore:
    """根据候选引用中的事实生成 Skill 匹配度建议评分。"""

    value = _unit((candidate.match_score * 0.72) + (candidate.readiness_score * 0.14) + (candidate.continuity_score * 0.14))
    return SkillMatchScore(
        score_ref=score_ref,
        value=value,
        confidence=0.8,
        reason_codes=(
            f"match={candidate.match_score:.3f}",
            f"readiness={candidate.readiness_score:.3f}",
            f"continuity={candidate.continuity_score:.3f}",
        ),
        evidence_refs=(candidate.candidate_ref, candidate.skill_ref),
    )


def build_tool_group_minimality_score(candidate: ToolGroupReleaseCandidate, score_ref: TypedRef | None = None) -> ToolGroupMinimalityScore:
    """根据工具组候选事实生成最小充分建议评分。"""

    missing_penalty = min(len(candidate.missing_tool_refs) * 0.12, 0.5)
    optional_penalty = min(len(candidate.optional_tool_refs) * 0.04, 0.2)
    value = _unit(candidate.minimality_score - missing_penalty - optional_penalty)
    return ToolGroupMinimalityScore(
        score_ref=score_ref,
        value=value,
        confidence=0.8,
        reason_codes=(
            f"minimality={candidate.minimality_score:.3f}",
            f"missing_tools={len(candidate.missing_tool_refs)}",
            f"optional_tools={len(candidate.optional_tool_refs)}",
        ),
        evidence_refs=(candidate.candidate_ref, candidate.tool_group_ref),
    )


def build_tool_exposure_cost_score(
    candidate: ToolGroupReleaseCandidate,
    affective_input: AffectiveWeightInput | None = None,
    dynamic_drive_input: DynamicDriveInput | None = None,
    score_ref: TypedRef | None = None,
) -> ToolExposureCostScore:
    """生成工具暴露成本建议评分；情感和动态驱动只改变倾向权重。"""

    caution = affective_input.caution_weight if affective_input is not None else 0.0
    pressure = dynamic_drive_input.risk_pressure_weight if dynamic_drive_input is not None else 0.0
    tool_count_pressure = min(len(candidate.tool_refs) * 0.03, 0.3)
    value = _unit((candidate.exposure_cost_score * 0.65) + (caution * 0.12) + (pressure * 0.13) + tool_count_pressure)
    return ToolExposureCostScore(
        score_ref=score_ref,
        value=value,
        confidence=0.8,
        reason_codes=(
            f"base_exposure={candidate.exposure_cost_score:.3f}",
            f"caution_weight={caution:.3f}",
            f"risk_pressure={pressure:.3f}",
            f"tool_refs={len(candidate.tool_refs)}",
        ),
        evidence_refs=(candidate.candidate_ref, candidate.tool_group_ref),
    )


def build_tool_group_sufficiency_score(candidate: ToolGroupReleaseCandidate, score_ref: TypedRef | None = None) -> ToolGroupSufficiencyScore:
    """生成工具组充分性建议评分。"""

    required = len(candidate.required_tool_refs)
    missing = len(candidate.missing_tool_refs)
    required_part = 1.0 if required == 0 else max(0.0, (required - missing) / required)
    value = _unit((candidate.sufficiency_score * 0.7) + (required_part * 0.3))
    return ToolGroupSufficiencyScore(
        score_ref=score_ref,
        value=value,
        confidence=0.8,
        reason_codes=(
            f"sufficiency={candidate.sufficiency_score:.3f}",
            f"required_tools={required}",
            f"missing_tools={missing}",
        ),
        evidence_refs=(candidate.candidate_ref, candidate.tool_group_ref),
    )


def build_reversibility_index(
    reversibility_hint: float,
    exposure_cost: ToolExposureCostScore | None = None,
    score_ref: TypedRef | None = None,
) -> ReversibilityIndex:
    """生成可逆性建议指数。"""

    cost_penalty = exposure_cost.value * 0.25 if exposure_cost is not None else 0.0
    value = _unit(reversibility_hint - cost_penalty)
    return ReversibilityIndex(
        score_ref=score_ref,
        value=value,
        confidence=0.8,
        reason_codes=(f"reversibility_hint={reversibility_hint:.3f}", f"cost_penalty={cost_penalty:.3f}"),
        evidence_refs=exposure_cost.evidence_refs if exposure_cost is not None else (),
    )


def build_stability_index(
    continuity_value: float,
    readiness_value: float,
    dynamic_drive_input: DynamicDriveInput | None = None,
    score_ref: TypedRef | None = None,
) -> StabilityIndex:
    """生成流程稳定性建议指数。"""

    stability_pressure = dynamic_drive_input.stability_pressure_weight if dynamic_drive_input is not None else 0.0
    value = _unit((continuity_value * 0.42) + (readiness_value * 0.38) + (stability_pressure * 0.2))
    return StabilityIndex(
        score_ref=score_ref,
        value=value,
        confidence=0.8,
        reason_codes=(
            f"continuity={continuity_value:.3f}",
            f"readiness={readiness_value:.3f}",
            f"stability_pressure={stability_pressure:.3f}",
        ),
    )


def build_skill_tool_math_score_vector(
    score_ref: TypedRef,
    scores: tuple[SkillToolScoreBase, ...],
    summary: str = "skill tool math score advice",
) -> MathScoreVector:
    """将第三阶段评分映射为第一阶段 MathScoreVector。"""

    if not scores:
        normalized = 0.0
    else:
        normalized = sum(item.value for item in scores) / len(scores)
    entries: list[tuple[str, float, ScoreDirection]] = []
    for item in scores:
        direction = ScoreDirection.COST if item.score_kind in {
            SkillToolScoreKind.TOOL_EXPOSURE_COST,
            SkillToolScoreKind.TOOL_GROUP_EXPOSURE_COST,
            SkillToolScoreKind.SKILL_RISK_AWARENESS,
        } else ScoreDirection.BENEFIT
        entries.append((item.score_kind.value, item.value, direction))
    return MathScoreVector(
        score_ref=score_ref,
        score_entries=tuple(entries),
        source_score_refs=tuple(item.score_ref for item in scores if item.score_ref is not None),
        normalized_score=round(_unit(normalized), 6),
        confidence=0.8 if scores else 0.0,
        penalty_total=round(sum(item.value for item in scores if item.score_kind in {
            SkillToolScoreKind.TOOL_EXPOSURE_COST,
            SkillToolScoreKind.TOOL_GROUP_EXPOSURE_COST,
            SkillToolScoreKind.SKILL_RISK_AWARENESS,
        }), 6),
        bonus_total=round(sum(item.value for item in scores if item.score_kind not in {
            SkillToolScoreKind.TOOL_EXPOSURE_COST,
            SkillToolScoreKind.TOOL_GROUP_EXPOSURE_COST,
            SkillToolScoreKind.SKILL_RISK_AWARENESS,
        }), 6),
        summary=summary,
    )
