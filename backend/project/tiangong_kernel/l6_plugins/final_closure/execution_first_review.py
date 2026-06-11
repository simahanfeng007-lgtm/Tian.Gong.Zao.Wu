"""L6 phase8 execution-first closure review contracts."""
from __future__ import annotations
from dataclasses import dataclass
from .common import FinalClosureArtifactBase, L6ExecutionFirstClosurePolicy

@dataclass(frozen=True)
class L6ExecutionFirstReviewReport(FinalClosureArtifactBase):
    object_ref: str = "report:l6_phase8_execution_first_review"
    policy: L6ExecutionFirstClosurePolicy = L6ExecutionFirstClosurePolicy()
    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.policy, L6ExecutionFirstClosurePolicy): raise ValueError("policy must be L6ExecutionFirstClosurePolicy")
@dataclass(frozen=True)
class L6LongChainCapabilitySummary(FinalClosureArtifactBase): object_ref: str = "summary:l6_phase8_long_chain_capability"
@dataclass(frozen=True)
class L6LowRiskContinuationCoverageReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_low_risk_continuation"
@dataclass(frozen=True)
class L6MinimalConfirmationCoverageReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_minimal_confirmation"
@dataclass(frozen=True)
class L6DegradedContinuationCoverageReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_degraded_continuation"
@dataclass(frozen=True)
class L6ExecutionBlockingRiskReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_execution_blocking_risk"
