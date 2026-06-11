"""L6 phase8 L7 readiness contracts."""
from __future__ import annotations
from dataclasses import dataclass
from .common import FinalClosureArtifactBase

@dataclass(frozen=True)
class L7ReadinessReport(FinalClosureArtifactBase):
    object_ref: str = "report:l6_phase8_l7_readiness"
    planning_allowed: bool = True
    implementation_freeze_allowed: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.planning_allowed or self.implementation_freeze_allowed: raise ValueError("L7 readiness only allows planning before L6 planner review and repair")
@dataclass(frozen=True)
class L7DependencyReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_l7_dependency"
@dataclass(frozen=True)
class L7BoundaryCarryoverReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_l7_boundary_carryover"
@dataclass(frozen=True)
class L7OpenQuestionBacklog(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_l7_open_question_backlog"
