from __future__ import annotations
from dataclasses import dataclass
from .common import AdaptiveArtifactBase

@dataclass(frozen=True)
class SelfIterationProposalCandidate(AdaptiveArtifactBase):
    object_ref: str = "suggestion:l6_phase7_self_iteration_proposal_candidate"
    applies_iteration: bool = False
    activates_version_slot: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.applies_iteration or self.activates_version_slot:
            raise ValueError("SelfIterationProposalCandidate is not iteration apply")

@dataclass(frozen=True)
class VersionSlotCandidate(AdaptiveArtifactBase):
    object_ref: str = "hotswitch:l6_phase7_version_slot_candidate"
    activated: bool = False

@dataclass(frozen=True)
class ChangeProposalCandidate(AdaptiveArtifactBase):
    object_ref: str = "suggestion:l6_phase7_change_proposal_candidate"

@dataclass(frozen=True)
class MergeReadinessRequirement(AdaptiveArtifactBase):
    object_ref: str = "requirement:l6_phase7_merge_readiness"

@dataclass(frozen=True)
class IterationRollbackRequirement(AdaptiveArtifactBase):
    object_ref: str = "rollback:l6_phase7_iteration_rollback_requirement"

@dataclass(frozen=True)
class IterationGovernanceReviewRequest(AdaptiveArtifactBase):
    object_ref: str = "review:l6_phase7_iteration_governance"

class SelfIterationProposalPlugin:
    declaration_ref = "decl:l6_phase7_self_iteration_proposal_plugin"
