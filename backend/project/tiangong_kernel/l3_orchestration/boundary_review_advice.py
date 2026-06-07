"""L3 第五阶段边界审查准备建议对象。

本模块只输出准备建议、需求提示与状态转移建议，不做 L5 真实裁决。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .boundary_request import BoundaryCheckEnvelope, BoundaryRequirementHint
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind


class BoundaryReviewAdviceKind(str, Enum):
    """边界审查建议类别。"""

    PREPARE = "prepare"
    COLLECT_EVIDENCE = "collect_evidence"
    CLARIFY = "clarify"
    WAIT = "wait"
    ROUTE = "route"
    STATE_TRANSITION = "state_transition"


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
class BoundaryPreparationAdvice:
    """边界请求准备建议；不提交审查。"""

    advice_ref: TypedRef
    envelope: BoundaryCheckEnvelope
    requirement_hints: tuple[BoundaryRequirementHint, ...] = field(default_factory=tuple)
    next_preparation_hint: str = "collect_missing_review_context"
    readiness_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.next_preparation_hint, "BoundaryPreparationAdvice.next_preparation_hint", 128)
        _ensure_unit_interval(self.readiness_hint, "BoundaryPreparationAdvice.readiness_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "BoundaryPreparationAdvice.reason_codes", 128)
        _ensure_short_text(self.reason_summary, "BoundaryPreparationAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "BoundaryPreparationAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("BoundaryPreparationAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryReviewAdvice:
    """边界审查路径建议；不包含真实审查结果。"""

    advice_ref: TypedRef
    envelope: BoundaryCheckEnvelope
    advice_kind: BoundaryReviewAdviceKind = BoundaryReviewAdviceKind.PREPARE
    preparation_advice: BoundaryPreparationAdvice | None = None
    related_path_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    route_ranking_ref: TypedRef | None = None
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "BoundaryReviewAdvice.confidence")
        _ensure_short_text(self.reason_summary, "BoundaryReviewAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "BoundaryReviewAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("BoundaryReviewAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryStateTransitionAdvice:
    """边界请求状态转移建议；不写入 L2 或 L5。"""

    advice_ref: TypedRef
    boundary_request_ref: TypedRef
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.CREATED
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.PREPARED
    transition_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.CONTINUE_CURRENT_STEP
    transition_score: float = 0.0
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.transition_score, "BoundaryStateTransitionAdvice.transition_score")
        _ensure_short_text(self.reason_summary, "BoundaryStateTransitionAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "BoundaryStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("BoundaryStateTransitionAdvice.schema_version cannot be empty")
