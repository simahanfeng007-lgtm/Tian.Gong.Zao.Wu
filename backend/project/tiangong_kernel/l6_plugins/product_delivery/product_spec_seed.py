"""Product specification seed candidates for L6 phase6."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import ProductArtifactBase, ensure_bool, ensure_ref_items, ensure_ref_text


@dataclass(frozen=True)
class ProductSpecSeedCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_spec_seed_candidate"
    seed_version_ref: str = "product:l6_phase6_seed_v1"
    requirement_gap_refs: tuple[str, ...] = field(default_factory=lambda: ("report:l6_phase6_requirement_gap",))
    conflict_report_refs: tuple[str, ...] = field(default_factory=lambda: ("report:l6_phase6_spec_conflict",))
    product_spec_finalized: bool = False
    artifact_materialization_requested: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.seed_version_ref, "ProductSpecSeedCandidate.seed_version_ref")
        ensure_ref_items(self.requirement_gap_refs, "ProductSpecSeedCandidate.requirement_gap_refs", required=True)
        ensure_ref_items(self.conflict_report_refs, "ProductSpecSeedCandidate.conflict_report_refs", required=True)
        ensure_bool(self.product_spec_finalized, "ProductSpecSeedCandidate.product_spec_finalized")
        ensure_bool(self.artifact_materialization_requested, "ProductSpecSeedCandidate.artifact_materialization_requested")
        if self.product_spec_finalized or self.artifact_materialization_requested:
            raise ValueError("ProductSpecSeedCandidate is a seed candidate only, not a finalized product spec or build request")


@dataclass(frozen=True)
class ProductSpecSeedPublicSummary(ProductArtifactBase):
    object_ref: str = "summary:l6_phase6_product_spec_seed_public"
    exposes_raw_context: bool = False
    exposes_private_memory: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.exposes_raw_context, "ProductSpecSeedPublicSummary.exposes_raw_context")
        ensure_bool(self.exposes_private_memory, "ProductSpecSeedPublicSummary.exposes_private_memory")
        if self.exposes_raw_context or self.exposes_private_memory:
            raise ValueError("ProductSpecSeedPublicSummary must stay minimal and redacted")


@dataclass(frozen=True)
class ProductRequirementGapReport(ProductArtifactBase):
    object_ref: str = "report:l6_phase6_product_requirement_gap"
    gap_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_gap_assumption",))
    blocks_delivery: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.gap_refs, "ProductRequirementGapReport.gap_refs", required=True)
        ensure_bool(self.blocks_delivery, "ProductRequirementGapReport.blocks_delivery")


@dataclass(frozen=True)
class ProductRequirementConflictReport(ProductArtifactBase):
    object_ref: str = "report:l6_phase6_product_requirement_conflict"
    conflict_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_conflict_ref",))
    needs_user_confirmation: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.conflict_refs, "ProductRequirementConflictReport.conflict_refs", required=True)
        ensure_bool(self.needs_user_confirmation, "ProductRequirementConflictReport.needs_user_confirmation")


@dataclass(frozen=True)
class ProductAssumptionList(ProductArtifactBase):
    object_ref: str = "summary:l6_phase6_product_assumption_list"
    assumption_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_default_engineering_assumption",))
    allows_continue: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.assumption_refs, "ProductAssumptionList.assumption_refs", required=True)
        ensure_bool(self.allows_continue, "ProductAssumptionList.allows_continue")
        if not self.allows_continue:
            raise ValueError("Low-risk product assumptions should support continuation rather than over-asking")


@dataclass(frozen=True)
class ProductAcceptanceIntentCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_acceptance_intent_candidate"
    acceptance_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_acceptance_standard",))
    real_acceptance_result: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.acceptance_refs, "ProductAcceptanceIntentCandidate.acceptance_refs", required=True)
        ensure_bool(self.real_acceptance_result, "ProductAcceptanceIntentCandidate.real_acceptance_result")
        if self.real_acceptance_result:
            raise ValueError("Acceptance intent candidate cannot claim real acceptance result")
