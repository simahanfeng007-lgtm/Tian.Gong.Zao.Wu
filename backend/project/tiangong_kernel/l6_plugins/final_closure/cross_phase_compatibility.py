"""L6 phase8 cross-phase compatibility contracts."""
from __future__ import annotations
from dataclasses import dataclass
from .common import FinalClosureArtifactBase

@dataclass(frozen=True)
class L6CrossPhaseCompatibilityMatrix(FinalClosureArtifactBase):
    object_ref: str = "l6:phase8_cross_phase_matrix"
    common_contract_compatible: bool = True
    requirement_projection_handoff_compatible: bool = True
    quality_gate_compatible: bool = True
    def __post_init__(self) -> None:
        super().__post_init__()
        if not (self.common_contract_compatible and self.requirement_projection_handoff_compatible and self.quality_gate_compatible):
            raise ValueError("L6 cross-phase compatibility cannot be false in closure candidate")
@dataclass(frozen=True)
class L6ContractCompatibilityReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_contract_compatibility"
@dataclass(frozen=True)
class L6RequirementCompatibilityReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_requirement_compatibility"
@dataclass(frozen=True)
class L6ProjectionCompatibilityReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_projection_compatibility"
@dataclass(frozen=True)
class L6HandoffCompatibilityReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_handoff_compatibility"
@dataclass(frozen=True)
class L6PublicProjectionCompatibilityReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_public_projection_compatibility"
@dataclass(frozen=True)
class L6QualityGateCompatibilityReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_quality_gate_compatibility"
