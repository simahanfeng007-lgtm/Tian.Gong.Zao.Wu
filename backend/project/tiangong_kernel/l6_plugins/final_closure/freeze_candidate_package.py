"""L6 phase8 candidate-freeze package contracts."""
from __future__ import annotations
from dataclasses import dataclass
from .common import FinalClosureArtifactBase

@dataclass(frozen=True)
class L6FreezeCandidateDecision(FinalClosureArtifactBase):
    object_ref: str = "quality:l6_phase8_freeze_candidate_decision"
    allow_l6_candidate_freeze: bool = True
    allow_final_freeze_before_review: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.allow_l6_candidate_freeze or self.allow_final_freeze_before_review: raise ValueError("Only candidate freeze is allowed before planner review and total repair")
@dataclass(frozen=True)
class L6PlannerReviewReadinessDecision(FinalClosureArtifactBase): object_ref: str = "quality:l6_phase8_planner_review_readiness"
@dataclass(frozen=True)
class L6UnifiedP0P1RiskSummary(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_p0_p1_risk_summary"
@dataclass(frozen=True)
class L6UnifiedP2P3Backlog(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_p2_p3_backlog"
@dataclass(frozen=True)
class L6UnifiedBlockingReason(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_blocking_reason"
