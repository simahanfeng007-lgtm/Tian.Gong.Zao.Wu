"""L6 phase8 final handoff contracts."""
from __future__ import annotations
from dataclasses import dataclass
from .common import FinalClosureArtifactBase

@dataclass(frozen=True)
class L6FinalHandoffEnvelope(FinalClosureArtifactBase): object_ref: str = "handoff:l6_phase8_final_handoff"
@dataclass(frozen=True)
class L6FinalValidationReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_final_validation"
@dataclass(frozen=True)
class L6FinalChangeList(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_final_change_list"
@dataclass(frozen=True)
class L6FinalTodoList(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_final_todo"
@dataclass(frozen=True)
class L6FinalRiskList(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_final_risk"
@dataclass(frozen=True)
class L6FinalFreezeCandidateManifest(FinalClosureArtifactBase): object_ref: str = "summary:l6_phase8_candidate_freeze_manifest"
