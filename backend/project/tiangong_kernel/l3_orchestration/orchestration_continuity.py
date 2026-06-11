"""L3 第二阶段连续性评分对象与确定性轻量评估函数。

评分只输出建议与解释；不得作为权限裁决、执行许可或状态写入。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import OrchestrationLifecycleKind
from .orchestration_math import MathScoreVector, ScoreDirection
from .orchestration_math_input import AffectiveWeightInput, DynamicDriveInput
from .orchestration_progress import RunProgressSnapshot, TaskProgressSnapshot
from .orchestration_step_sequence import StepSequence, StepTransitionCandidate
from .orchestration_turn import TurnCarryoverHint


class ContinuityScoreKind(str, Enum):
    """连续性评分类别。"""

    UNKNOWN = "unknown"
    CONTINUITY_INDEX = "continuity_index"
    RESUMABILITY_INDEX = "resumability_index"
    INTERRUPTION_SEVERITY = "interruption_severity"
    STEP_READINESS = "step_readiness"
    PROGRESS_COHERENCE = "progress_coherence"
    CONTEXT_CARRYOVER = "context_carryover"
    RECOVERY_PRIORITY = "recovery_priority"
    CANCELLATION_SUITABILITY = "cancellation_suitability"


def _unit(value: float, field_name: str) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class ContinuityScoreBase:
    """连续性评分基础事实。"""

    score_ref: TypedRef | None = None
    score_kind: ContinuityScoreKind = ContinuityScoreKind.UNKNOWN
    value: float = 0.0
    confidence: float = 0.0
    reason_items: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.value, f"{type(self).__name__}.value")
        _ensure_unit_interval(self.confidence, f"{type(self).__name__}.confidence")
        if self.advisory_only is not True:
            raise ValueError(f"{type(self).__name__}.advisory_only must remain true in L3 phase 2")
        if any(len(item) > 256 for item in self.reason_items):
            raise ValueError(f"{type(self).__name__}.reason_items entries must be short")
        if not self.schema_version:
            raise ValueError(f"{type(self).__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContinuityIndex(ContinuityScoreBase):
    """流程连续性指数。"""

    score_kind: ContinuityScoreKind = ContinuityScoreKind.CONTINUITY_INDEX


@dataclass(frozen=True, slots=True)
class ResumabilityIndex(ContinuityScoreBase):
    """流程续接性指数。"""

    score_kind: ContinuityScoreKind = ContinuityScoreKind.RESUMABILITY_INDEX


@dataclass(frozen=True, slots=True)
class InterruptionSeverityScore(ContinuityScoreBase):
    """中断严重度评分。"""

    score_kind: ContinuityScoreKind = ContinuityScoreKind.INTERRUPTION_SEVERITY


@dataclass(frozen=True, slots=True)
class StepReadinessScore(ContinuityScoreBase):
    """Step 准备度评分；只判断编排条件。"""

    score_kind: ContinuityScoreKind = ContinuityScoreKind.STEP_READINESS


@dataclass(frozen=True, slots=True)
class ProgressCoherenceScore(ContinuityScoreBase):
    """进度自洽性评分。"""

    score_kind: ContinuityScoreKind = ContinuityScoreKind.PROGRESS_COHERENCE


@dataclass(frozen=True, slots=True)
class ContextCarryoverScore(ContinuityScoreBase):
    """Turn 间上下文续接价值评分。"""

    score_kind: ContinuityScoreKind = ContinuityScoreKind.CONTEXT_CARRYOVER


@dataclass(frozen=True, slots=True)
class RecoveryPriorityScore(ContinuityScoreBase):
    """恢复路径优先级评分。"""

    score_kind: ContinuityScoreKind = ContinuityScoreKind.RECOVERY_PRIORITY


@dataclass(frozen=True, slots=True)
class CancellationSuitabilityScore(ContinuityScoreBase):
    """取消或放弃适宜性评分。"""

    score_kind: ContinuityScoreKind = ContinuityScoreKind.CANCELLATION_SUITABILITY


@dataclass(frozen=True, slots=True)
class ContinuityEvaluationSet:
    """Run / Task / Turn / Step 连续性评分集合。"""

    evaluation_ref: TypedRef | None = None
    subject_ref: TypedRef | None = None
    continuity_index: ContinuityIndex | None = None
    resumability_index: ResumabilityIndex | None = None
    interruption_severity: InterruptionSeverityScore | None = None
    step_readiness: StepReadinessScore | None = None
    progress_coherence: ProgressCoherenceScore | None = None
    context_carryover: ContextCarryoverScore | None = None
    recovery_priority: RecoveryPriorityScore | None = None
    cancellation_suitability: CancellationSuitabilityScore | None = None
    math_score_vector: MathScoreVector | None = None
    affective_input: AffectiveWeightInput | None = None
    dynamic_drive_input: DynamicDriveInput | None = None
    advisory_only: bool = True
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("ContinuityEvaluationSet.advisory_only must remain true in L3 phase 2")
        if len(self.summary) > 512:
            raise ValueError("ContinuityEvaluationSet.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ContinuityEvaluationSet.schema_version cannot be empty")


def build_continuity_index(
    step_sequence: StepSequence,
    carryover_hints: tuple[TurnCarryoverHint, ...] = (),
    missing_state_fields: tuple[str, ...] = (),
) -> ContinuityIndex:
    """生成连续性指数；只使用已给内存对象。"""

    total = len(step_sequence.step_refs)
    completed = len(step_sequence.completed_step_refs)
    sequence_part = 1.0 if total == 0 else completed / total
    active_bonus = 0.2 if step_sequence.active_step_ref is not None else 0.0
    carryover_bonus = min(len(carryover_hints) * 0.1, 0.2)
    missing_penalty = min(len(missing_state_fields) * 0.15, 0.6)
    value = _unit(sequence_part + active_bonus + carryover_bonus - missing_penalty, "continuity")
    reasons = (
        f"step_sequence={completed}/{total}",
        f"carryover_hints={len(carryover_hints)}",
        f"missing_state_fields={len(missing_state_fields)}",
    )
    return ContinuityIndex(value=value, confidence=0.8, reason_items=reasons)


def build_resumability_index(
    lifecycle: OrchestrationLifecycleKind,
    next_step_refs: tuple[TypedRef, ...] = (),
    missing_state_fields: tuple[str, ...] = (),
    blocker_refs: tuple[TypedRef, ...] = (),
) -> ResumabilityIndex:
    """生成续接性指数；只评估是否适合续接。"""

    lifecycle_base = {
        OrchestrationLifecycleKind.ACTIVE: 0.75,
        OrchestrationLifecycleKind.WAITING: 0.65,
        OrchestrationLifecycleKind.PAUSED: 0.8,
        OrchestrationLifecycleKind.BLOCKED: 0.35,
        OrchestrationLifecycleKind.FAILED: 0.45,
        OrchestrationLifecycleKind.CANCELLED: 0.1,
        OrchestrationLifecycleKind.COMPLETED: 0.2,
        OrchestrationLifecycleKind.RESUMABLE: 0.9,
        OrchestrationLifecycleKind.ABANDONED: 0.05,
    }.get(lifecycle, 0.4)
    next_bonus = min(len(next_step_refs) * 0.1, 0.2)
    missing_penalty = min(len(missing_state_fields) * 0.12, 0.5)
    blocker_penalty = min(len(blocker_refs) * 0.18, 0.6)
    value = _unit(lifecycle_base + next_bonus - missing_penalty - blocker_penalty, "resumability")
    reasons = (
        f"lifecycle={lifecycle.value}",
        f"next_step_refs={len(next_step_refs)}",
        f"missing_state_fields={len(missing_state_fields)}",
        f"blocker_refs={len(blocker_refs)}",
    )
    return ResumabilityIndex(value=value, confidence=0.8, reason_items=reasons)


def build_interruption_severity_score(
    lifecycle: OrchestrationLifecycleKind,
    blocker_refs: tuple[TypedRef, ...] = (),
    failure_refs: tuple[TypedRef, ...] = (),
) -> InterruptionSeverityScore:
    """生成中断严重度评分。"""

    base = {
        OrchestrationLifecycleKind.ACTIVE: 0.1,
        OrchestrationLifecycleKind.WAITING: 0.25,
        OrchestrationLifecycleKind.PAUSED: 0.3,
        OrchestrationLifecycleKind.BLOCKED: 0.7,
        OrchestrationLifecycleKind.FAILED: 0.85,
        OrchestrationLifecycleKind.CANCELLED: 0.75,
        OrchestrationLifecycleKind.COMPLETED: 0.0,
        OrchestrationLifecycleKind.ABANDONED: 0.9,
    }.get(lifecycle, 0.4)
    value = _unit(base + min(len(blocker_refs) * 0.1, 0.2) + min(len(failure_refs) * 0.1, 0.2), "severity")
    reasons = (f"lifecycle={lifecycle.value}", f"blocker_refs={len(blocker_refs)}", f"failure_refs={len(failure_refs)}")
    return InterruptionSeverityScore(value=value, confidence=0.8, reason_items=reasons)


def build_step_readiness_score(
    candidate: StepTransitionCandidate,
    available_state_refs: tuple[TypedRef, ...] = (),
) -> StepReadinessScore:
    """生成 Step 准备度评分；只检查编排引用完整度。"""

    required = len(candidate.required_state_refs)
    available = len(available_state_refs)
    state_part = 1.0 if required == 0 else min(available / required, 1.0)
    missing_penalty = min(len(candidate.missing_state_fields) * 0.18, 0.7)
    blocker_penalty = min(len(candidate.blocker_refs) * 0.2, 0.7)
    value = _unit((state_part * 0.7) + (candidate.score_hint * 0.3) - missing_penalty - blocker_penalty, "readiness")
    reasons = (
        f"required_state_refs={required}",
        f"available_state_refs={available}",
        f"missing_state_fields={len(candidate.missing_state_fields)}",
        f"blocker_refs={len(candidate.blocker_refs)}",
    )
    return StepReadinessScore(value=value, confidence=0.8, reason_items=reasons)


def build_progress_coherence_score(
    step_sequence: StepSequence,
    task_snapshot: TaskProgressSnapshot | None = None,
    run_snapshot: RunProgressSnapshot | None = None,
) -> ProgressCoherenceScore:
    """生成进度自洽评分；只比较已给快照。"""

    duplicate_penalty = 0.0 if len(step_sequence.step_refs) == len(tuple(dict.fromkeys(step_sequence.step_refs))) else 0.3
    task_gap = 0.0
    if task_snapshot is not None:
        expected = len(task_snapshot.completed_step_refs)
        actual = len(step_sequence.completed_step_refs)
        task_gap = min(abs(expected - actual) * 0.1, 0.3)
    run_gap = 0.0
    if run_snapshot is not None and task_snapshot is not None and task_snapshot.task_ref is not None:
        run_gap = 0.0 if task_snapshot.task_ref in run_snapshot.task_refs else 0.2
    value = _unit(1.0 - duplicate_penalty - task_gap - run_gap, "progress_coherence")
    reasons = (f"duplicate_penalty={duplicate_penalty:.2f}", f"task_gap={task_gap:.2f}", f"run_gap={run_gap:.2f}")
    return ProgressCoherenceScore(value=value, confidence=0.8, reason_items=reasons)


def build_context_carryover_score(carryover_hints: tuple[TurnCarryoverHint, ...] = ()) -> ContextCarryoverScore:
    """生成 Turn 间上下文续接价值评分。"""

    if not carryover_hints:
        return ContextCarryoverScore(value=0.0, confidence=0.7, reason_items=("carryover_hints=0",))
    weighted_total = sum(item.carryover_value * item.confidence for item in carryover_hints)
    confidence_total = sum(item.confidence for item in carryover_hints) or 1.0
    value = _unit(weighted_total / confidence_total, "context_carryover")
    reasons = (f"carryover_hints={len(carryover_hints)}", f"weighted_value={value:.2f}")
    return ContextCarryoverScore(value=value, confidence=0.8, reason_items=reasons)


def build_recovery_priority_score(
    severity: InterruptionSeverityScore,
    resumability: ResumabilityIndex,
    dynamic_drive_input: DynamicDriveInput | None = None,
    affective_input: AffectiveWeightInput | None = None,
) -> RecoveryPriorityScore:
    """生成恢复路径优先级；动态驱动与情感只影响权重。"""

    dynamic_bonus = 0.0 if dynamic_drive_input is None else dynamic_drive_input.priority_weight * 0.15
    persistence_bonus = 0.0 if affective_input is None else affective_input.persistence_weight * 0.1
    value = _unit((severity.value * 0.45) + (resumability.value * 0.4) + dynamic_bonus + persistence_bonus, "recovery_priority")
    reasons = (
        f"severity={severity.value:.2f}",
        f"resumability={resumability.value:.2f}",
        f"dynamic_bonus={dynamic_bonus:.2f}",
        f"persistence_bonus={persistence_bonus:.2f}",
    )
    return RecoveryPriorityScore(value=value, confidence=0.8, reason_items=reasons)


def build_cancellation_suitability_score(
    severity: InterruptionSeverityScore,
    resumability: ResumabilityIndex,
    progress_coherence: ProgressCoherenceScore,
) -> CancellationSuitabilityScore:
    """生成取消适宜性建议；不执行取消。"""

    value = _unit((severity.value * 0.5) + ((1.0 - resumability.value) * 0.3) + ((1.0 - progress_coherence.value) * 0.2), "cancellation")
    reasons = (
        f"severity={severity.value:.2f}",
        f"resumability={resumability.value:.2f}",
        f"progress_coherence={progress_coherence.value:.2f}",
    )
    return CancellationSuitabilityScore(value=value, confidence=0.8, reason_items=reasons)


def build_math_score_vector_from_continuity(
    evaluation: ContinuityEvaluationSet,
    score_ref: TypedRef | None = None,
) -> MathScoreVector:
    """把连续性评分映射到第一阶段 MathScoreVector；仍只是评分事实。"""

    score_items: list[tuple[str, float, ScoreDirection]] = []
    for item in (
        evaluation.continuity_index,
        evaluation.resumability_index,
        evaluation.step_readiness,
        evaluation.progress_coherence,
        evaluation.context_carryover,
        evaluation.recovery_priority,
    ):
        if item is not None:
            score_items.append((item.score_kind.value, item.value, ScoreDirection.BENEFIT))
    if evaluation.interruption_severity is not None:
        score_items.append((evaluation.interruption_severity.score_kind.value, evaluation.interruption_severity.value, ScoreDirection.COST))
    if evaluation.cancellation_suitability is not None:
        score_items.append((evaluation.cancellation_suitability.score_kind.value, evaluation.cancellation_suitability.value, ScoreDirection.NEUTRAL))
    normalized = 0.0 if not score_items else sum(value for _name, value, _direction in score_items) / len(score_items)
    return MathScoreVector(
        score_ref=score_ref,
        score_entries=tuple(score_items),
        normalized_score=_unit(normalized, "normalized"),
        confidence=0.8 if score_items else 0.0,
        summary="phase2 continuity score vector",
    )


def order_resume_candidates(
    candidates: tuple[StepTransitionCandidate, ...],
    readiness_scores: tuple[tuple[TypedRef, float], ...] = (),
) -> tuple[StepTransitionCandidate, ...]:
    """按准备度提示返回候选顺序；只返回排序后的内存元组。"""

    score_map = {ref: value for ref, value in readiness_scores}
    return tuple(
        sorted(
            candidates,
            key=lambda item: score_map.get(item.candidate_ref, item.score_hint),
            reverse=True,
        )
    )
