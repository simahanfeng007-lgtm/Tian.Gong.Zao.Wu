from __future__ import annotations
from dataclasses import dataclass
from .common import AdaptiveArtifactBase

@dataclass(frozen=True)
class EvolutionCandidateReviewEnvelope(AdaptiveArtifactBase):
    object_ref: str = "review:l6_phase7_evolution_candidate_review"
    executes_evolution: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.executes_evolution:
            raise ValueError("EvolutionCandidateReviewEnvelope is not evolution execution")

@dataclass(frozen=True)
class EvolutionBenefitRiskProjection(AdaptiveArtifactBase):
    object_ref: str = "projection:l6_phase7_evolution_benefit_risk"

@dataclass(frozen=True)
class EvolutionGovernanceRequirement(AdaptiveArtifactBase):
    object_ref: str = "requirement:l6_phase7_evolution_governance"

@dataclass(frozen=True)
class EvolutionRollbackRequirement(AdaptiveArtifactBase):
    object_ref: str = "rollback:l6_phase7_evolution_rollback_requirement"

@dataclass(frozen=True)
class EvolutionHumanGateRequirement(AdaptiveArtifactBase):
    object_ref: str = "requirement:l6_phase7_evolution_human_gate"

class EvolutionCandidateReviewPlugin:
    declaration_ref = "decl:l6_phase7_evolution_candidate_review_plugin"
