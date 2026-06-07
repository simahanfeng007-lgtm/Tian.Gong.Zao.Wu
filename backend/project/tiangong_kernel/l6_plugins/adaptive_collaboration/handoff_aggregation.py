from __future__ import annotations
from dataclasses import dataclass
from .common import AdaptiveArtifactBase

@dataclass(frozen=True)
class HandoffAggregationCandidate(AdaptiveArtifactBase):
    object_ref: str = "handoff:l6_phase7_handoff_aggregation_candidate"
    auto_merges: bool = False
    result_as_fact: bool = False
    orphan_detected_ref: str = "handoff:l6_phase7_orphan_check"
    stale_detected_ref: str = "handoff:l6_phase7_stale_check"
    duplicate_detected_ref: str = "handoff:l6_phase7_duplicate_check"
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.auto_merges or self.result_as_fact:
            raise ValueError("HandoffAggregationCandidate is not auto merge or fact admission")

@dataclass(frozen=True)
class HandoffConflictReport(AdaptiveArtifactBase):
    object_ref: str = "report:l6_phase7_handoff_conflict"

@dataclass(frozen=True)
class HandoffGapReport(AdaptiveArtifactBase):
    object_ref: str = "report:l6_phase7_handoff_gap"

@dataclass(frozen=True)
class HandoffResultSummary(AdaptiveArtifactBase):
    object_ref: str = "summary:l6_phase7_handoff_result"

@dataclass(frozen=True)
class HandoffContinuationSuggestion(AdaptiveArtifactBase):
    object_ref: str = "suggestion:l6_phase7_handoff_continuation"

class HandoffAggregationPlugin:
    declaration_ref = "decl:l6_phase7_handoff_aggregation_plugin"
