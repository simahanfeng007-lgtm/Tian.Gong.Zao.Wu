from __future__ import annotations
from dataclasses import dataclass
from .common import AdaptiveArtifactBase

@dataclass(frozen=True)
class ConflictResolutionSuggestion(AdaptiveArtifactBase):
    object_ref: str = "suggestion:l6_phase7_conflict_resolution"
    final_decision: bool = False
    overwrites_fact: bool = False
    deletes_candidate: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.final_decision or self.overwrites_fact or self.deletes_candidate:
            raise ValueError("ConflictResolutionSuggestion is not final decision, fact overwrite, or deletion")

@dataclass(frozen=True)
class ConflictEvidenceIndex(AdaptiveArtifactBase):
    object_ref: str = "evidence:l6_phase7_conflict_evidence"

@dataclass(frozen=True)
class ConflictSeverityHint(AdaptiveArtifactBase):
    object_ref: str = "hint:l6_phase7_conflict_severity"

@dataclass(frozen=True)
class ConflictReviewRequest(AdaptiveArtifactBase):
    object_ref: str = "review:l6_phase7_conflict_review"

@dataclass(frozen=True)
class ConflictDegradationSuggestion(AdaptiveArtifactBase):
    object_ref: str = "suggestion:l6_phase7_conflict_degradation"

class ConflictResolutionSuggestionPlugin:
    declaration_ref = "decl:l6_phase7_conflict_resolution_suggestion_plugin"
