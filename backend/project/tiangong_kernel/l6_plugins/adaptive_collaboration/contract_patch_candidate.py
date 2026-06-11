from __future__ import annotations
from dataclasses import dataclass
from .common import AdaptiveArtifactBase

@dataclass(frozen=True)
class ContractPatchCandidate(AdaptiveArtifactBase):
    object_ref: str = "suggestion:l6_phase7_contract_patch_candidate"
    applies_contract_patch: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.applies_contract_patch:
            raise ValueError("ContractPatchCandidate is not a contract patch")

@dataclass(frozen=True)
class ContractPatchImpactAssessmentCandidate(AdaptiveArtifactBase):
    object_ref: str = "report:l6_phase7_contract_patch_impact_assessment"

@dataclass(frozen=True)
class CompatibilityMatrixRequirement(AdaptiveArtifactBase):
    object_ref: str = "requirement:l6_phase7_compatibility_matrix"

@dataclass(frozen=True)
class MigrationRequirement(AdaptiveArtifactBase):
    object_ref: str = "migration:l6_phase7_migration_requirement"
    performs_migration: bool = False

@dataclass(frozen=True)
class RollbackRequirement(AdaptiveArtifactBase):
    object_ref: str = "rollback:l6_phase7_rollback_requirement"
    performs_rollback: bool = False

@dataclass(frozen=True)
class ReplayCompatibilityRequirement(AdaptiveArtifactBase):
    object_ref: str = "requirement:l6_phase7_replay_compatibility"

class ContractPatchCandidatePlugin:
    declaration_ref = "decl:l6_phase7_contract_patch_candidate_plugin"
