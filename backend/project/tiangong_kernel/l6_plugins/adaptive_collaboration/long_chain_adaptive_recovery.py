from __future__ import annotations
from dataclasses import dataclass
from .common import AdaptiveArtifactBase

@dataclass(frozen=True)
class LongChainAdaptiveRecoveryPlan(AdaptiveArtifactBase):
    object_ref: str = "checkpoint:l6_phase7_long_chain_adaptive_recovery_plan"
    scheduler_state: bool = False
    aborts_by_default: bool = False
    has_low_cost_continuation: bool = True
    current_stage_ref: str = "checkpoint:l6_phase7_current_stage"
    failure_point_ref: str = "report:l6_phase7_failure_point"
    recommended_next_step_ref: str = "suggestion:l6_phase7_next_step"
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.scheduler_state or self.aborts_by_default or not self.has_low_cost_continuation:
            raise ValueError("LongChainAdaptiveRecoveryPlan is not scheduler state and must recover, not abort")

@dataclass(frozen=True)
class StageRecoverySuggestion(AdaptiveArtifactBase):
    object_ref: str = "suggestion:l6_phase7_stage_recovery"

@dataclass(frozen=True)
class LowCostContinuationHint(AdaptiveArtifactBase):
    object_ref: str = "hint:l6_phase7_low_cost_continuation"

@dataclass(frozen=True)
class BranchCompressionSuggestion(AdaptiveArtifactBase):
    object_ref: str = "suggestion:l6_phase7_branch_compression"

@dataclass(frozen=True)
class NextIterationHint(AdaptiveArtifactBase):
    object_ref: str = "hint:l6_phase7_next_iteration"

@dataclass(frozen=True)
class AdaptiveCheckpointContinuationHint(AdaptiveArtifactBase):
    object_ref: str = "checkpoint:l6_phase7_adaptive_continuation_hint"

@dataclass(frozen=True)
class LongChainLearningLoopHint(AdaptiveArtifactBase):
    object_ref: str = "hint:l6_phase7_long_chain_learning_loop"

@dataclass(frozen=True)
class LongChainRepairLoopHint(AdaptiveArtifactBase):
    object_ref: str = "hint:l6_phase7_long_chain_repair_loop"

class LongChainAdaptiveRecoveryPlugin:
    declaration_ref = "decl:l6_phase7_long_chain_adaptive_recovery_plugin"
