"""Long-chain production candidate declarations for L6 phase6."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import ProductArtifactBase, ensure_bool, ensure_non_negative_int, ensure_ref_items


@dataclass(frozen=True)
class ProductionStageCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_production_stage_candidate"
    stage_index: int = 0
    stage_summary_ref: str = "summary:l6_phase6_stage"

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_non_negative_int(self.stage_index, "ProductionStageCandidate.stage_index")


@dataclass(frozen=True)
class ProductCheckpointHint(ProductArtifactBase):
    object_ref: str = "checkpoint:l6_phase6_product_checkpoint_hint"
    completed_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_completed",))
    pending_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_pending",))
    scheduler_state: bool = False
    persisted_checkpoint: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.completed_summary_refs, "ProductCheckpointHint.completed_summary_refs", required=True)
        ensure_ref_items(self.pending_summary_refs, "ProductCheckpointHint.pending_summary_refs", required=True)
        ensure_bool(self.scheduler_state, "ProductCheckpointHint.scheduler_state")
        ensure_bool(self.persisted_checkpoint, "ProductCheckpointHint.persisted_checkpoint")
        if self.scheduler_state or self.persisted_checkpoint:
            raise ValueError("ProductCheckpointHint is not scheduler state or persisted checkpoint")


@dataclass(frozen=True)
class IntermediateArtifactSummary(ProductArtifactBase):
    object_ref: str = "summary:l6_phase6_intermediate_artifact"
    artifact_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_intermediate_candidate",))
    claims_materialized: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.artifact_refs, "IntermediateArtifactSummary.artifact_refs", required=True)
        ensure_bool(self.claims_materialized, "IntermediateArtifactSummary.claims_materialized")
        if self.claims_materialized:
            raise ValueError("IntermediateArtifactSummary cannot claim materialized artifacts")


@dataclass(frozen=True)
class ProductionContinuationHint(ProductArtifactBase):
    object_ref: str = "hint:l6_phase6_production_continuation"
    continue_when_low_risk: bool = True
    governance_review_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.continue_when_low_risk, "ProductionContinuationHint.continue_when_low_risk")
        ensure_bool(self.governance_review_required, "ProductionContinuationHint.governance_review_required")
        if not self.continue_when_low_risk or not self.governance_review_required:
            raise ValueError("ProductionContinuationHint must continue low-risk work through governance")


@dataclass(frozen=True)
class ProductionRecoverySuggestion(ProductArtifactBase):
    object_ref: str = "suggestion:l6_phase6_production_recovery"
    recovery_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_recovery_step",))
    aborts_by_default: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.recovery_refs, "ProductionRecoverySuggestion.recovery_refs", required=True)
        ensure_bool(self.aborts_by_default, "ProductionRecoverySuggestion.aborts_by_default")
        if self.aborts_by_default:
            raise ValueError("Production failure should recover, not abort by default")


@dataclass(frozen=True)
class ProductionDegradedContinuationSuggestion(ProductArtifactBase):
    object_ref: str = "suggestion:l6_phase6_degraded_continuation"
    degradation_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_degraded_path",))
    stops_task: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.degradation_refs, "ProductionDegradedContinuationSuggestion.degradation_refs", required=True)
        ensure_bool(self.stops_task, "ProductionDegradedContinuationSuggestion.stops_task")
        if self.stops_task:
            raise ValueError("Degraded continuation cannot stop a legal product task")


@dataclass(frozen=True)
class ProductionMinimalConfirmationPolicy(ProductArtifactBase):
    object_ref: str = "policy:l6_phase6_production_minimal_confirmation"
    batch_when_safe: bool = True
    defer_low_risk_questions: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.batch_when_safe, "ProductionMinimalConfirmationPolicy.batch_when_safe")
        ensure_bool(self.defer_low_risk_questions, "ProductionMinimalConfirmationPolicy.defer_low_risk_questions")
        if not self.batch_when_safe or not self.defer_low_risk_questions:
            raise ValueError("Production minimal confirmation must batch/defer safe questions")


@dataclass(frozen=True)
class ProductionLongChainState(ProductArtifactBase):
    object_ref: str = "state:l6_phase6_production_long_chain_candidate"
    checkpoint_refs: tuple[str, ...] = field(default_factory=lambda: ("checkpoint:l6_phase6_product_checkpoint_hint",))
    real_scheduler_state: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.checkpoint_refs, "ProductionLongChainState.checkpoint_refs", required=True)
        ensure_bool(self.real_scheduler_state, "ProductionLongChainState.real_scheduler_state")
        if self.real_scheduler_state:
            raise ValueError("ProductionLongChainState cannot be scheduler state")


@dataclass(frozen=True)
class ProductionProgressDigest(ProductArtifactBase):
    object_ref: str = "digest:l6_phase6_production_progress"
    progress_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_progress",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.progress_summary_refs, "ProductionProgressDigest.progress_summary_refs", required=True)
