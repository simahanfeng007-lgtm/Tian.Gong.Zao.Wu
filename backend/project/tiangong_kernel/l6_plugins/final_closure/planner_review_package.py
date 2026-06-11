"""L6 phase8 planner-review package contracts."""
from __future__ import annotations
from dataclasses import dataclass, field
from .common import FinalClosureArtifactBase, PlannerRole, ensure_non_negative_int

ALL_PLANNER_ROLES = tuple(role for role in PlannerRole)

@dataclass(frozen=True)
class L6PlannerReviewPackage(FinalClosureArtifactBase):
    object_ref: str = "review:l6_phase8_planner_review_package"
    role_refs: tuple[str, ...] = field(default_factory=lambda: tuple(f"review:{role.value}" for role in ALL_PLANNER_ROLES))
    role_count: int = 18
    output_template_ref: str = "summary:l6_phase8_planner_review_output_template"
    def __post_init__(self) -> None:
        super().__post_init__(); ensure_non_negative_int(self.role_count, "role_count")
        if self.role_count != 18 or len(self.role_refs) != 18: raise ValueError("Planner review package must cover 18 roles")
@dataclass(frozen=True)
class L6PlannerReviewIndex(L6PlannerReviewPackage): object_ref: str = "review:l6_phase8_planner_review_index"
@dataclass(frozen=True)
class L6PlannerReviewPrompt(L6PlannerReviewPackage): object_ref: str = "review:l6_phase8_planner_review_prompt"
@dataclass(frozen=True)
class L6PlannerReviewChecklist(L6PlannerReviewPackage): object_ref: str = "review:l6_phase8_planner_review_checklist"
@dataclass(frozen=True)
class L6PlannerRoleCoverageMatrix(L6PlannerReviewPackage): object_ref: str = "review:l6_phase8_planner_role_coverage"
@dataclass(frozen=True)
class L6PlannerReviewRiskMatrix(L6PlannerReviewPackage): object_ref: str = "review:l6_phase8_planner_risk_matrix"
@dataclass(frozen=True)
class L6PlannerReviewSubmissionGuide(L6PlannerReviewPackage): object_ref: str = "review:l6_phase8_planner_submission_guide"
