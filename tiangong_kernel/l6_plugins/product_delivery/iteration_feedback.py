"""Product iteration feedback candidates for L6 phase6."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import ProductArtifactBase, ensure_bool, ensure_ref_items


@dataclass(frozen=True)
class ProductIterationCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_iteration_candidate"
    feedback_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_feedback",))
    starts_iteration: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.feedback_refs, "ProductIterationCandidate.feedback_refs", required=True)
        ensure_bool(self.starts_iteration, "ProductIterationCandidate.starts_iteration")
        if self.starts_iteration:
            raise ValueError("ProductIterationCandidate cannot start an iteration by itself")


@dataclass(frozen=True)
class ProductRepairSuggestion(ProductArtifactBase):
    object_ref: str = "suggestion:l6_phase6_product_repair"
    repair_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_repair_candidate",))
    applies_repair: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.repair_refs, "ProductRepairSuggestion.repair_refs", required=True)
        ensure_bool(self.applies_repair, "ProductRepairSuggestion.applies_repair")
        if self.applies_repair:
            raise ValueError("ProductRepairSuggestion cannot apply repairs")


@dataclass(frozen=True)
class ProductOptimizationSuggestion(ProductArtifactBase):
    object_ref: str = "suggestion:l6_phase6_product_optimization"
    optimization_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_optimization",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.optimization_refs, "ProductOptimizationSuggestion.optimization_refs", required=True)


@dataclass(frozen=True)
class ProductFeedbackIncorporationHint(ProductArtifactBase):
    object_ref: str = "hint:l6_phase6_feedback_incorporation"
    feedback_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_user_feedback",))
    modifies_common_contract: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.feedback_summary_refs, "ProductFeedbackIncorporationHint.feedback_summary_refs", required=True)
        ensure_bool(self.modifies_common_contract, "ProductFeedbackIncorporationHint.modifies_common_contract")
        if self.modifies_common_contract:
            raise ValueError("ProductFeedbackIncorporationHint cannot modify public contracts")


@dataclass(frozen=True)
class NextDeliveryCycleHint(ProductArtifactBase):
    object_ref: str = "hint:l6_phase6_next_delivery_cycle"
    next_step_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_next_cycle",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.next_step_refs, "NextDeliveryCycleHint.next_step_refs", required=True)
