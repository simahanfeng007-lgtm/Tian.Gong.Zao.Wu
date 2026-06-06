"""Product quality gate candidates for L6 phase6."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import ProductArtifactBase, ensure_bool, ensure_ref_items


@dataclass(frozen=True)
class ProductQualityGateCandidate(ProductArtifactBase):
    object_ref: str = "quality:l6_phase6_product_quality_gate_candidate"
    check_refs: tuple[str, ...] = field(default_factory=lambda: ("quality:l6_phase6_completeness", "quality:l6_phase6_consistency"))
    claims_passed_result: bool = False
    claims_real_test_result: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.check_refs, "ProductQualityGateCandidate.check_refs", required=True)
        ensure_bool(self.claims_passed_result, "ProductQualityGateCandidate.claims_passed_result")
        ensure_bool(self.claims_real_test_result, "ProductQualityGateCandidate.claims_real_test_result")
        if self.claims_passed_result or self.claims_real_test_result:
            raise ValueError("ProductQualityGateCandidate cannot claim real pass or test results")


@dataclass(frozen=True)
class ProductCompletenessCheck(ProductArtifactBase):
    object_ref: str = "quality:l6_phase6_product_completeness_check"
    missing_item_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.missing_item_refs, "ProductCompletenessCheck.missing_item_refs")


@dataclass(frozen=True)
class ProductConsistencyCheck(ProductArtifactBase):
    object_ref: str = "quality:l6_phase6_product_consistency_check"
    inconsistency_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.inconsistency_refs, "ProductConsistencyCheck.inconsistency_refs")


@dataclass(frozen=True)
class ProductAcceptanceChecklist(ProductArtifactBase):
    object_ref: str = "quality:l6_phase6_product_acceptance_checklist"
    acceptance_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_acceptance_item",))
    real_acceptance_performed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.acceptance_refs, "ProductAcceptanceChecklist.acceptance_refs", required=True)
        ensure_bool(self.real_acceptance_performed, "ProductAcceptanceChecklist.real_acceptance_performed")
        if self.real_acceptance_performed:
            raise ValueError("ProductAcceptanceChecklist is not real acceptance execution")


@dataclass(frozen=True)
class ProductRegressionRiskHint(ProductArtifactBase):
    object_ref: str = "hint:l6_phase6_product_regression_risk"
    regression_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_regression_risk",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.regression_refs, "ProductRegressionRiskHint.regression_refs", required=True)


@dataclass(frozen=True)
class ProductUnfinishedItemsCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_unfinished_items_candidate"
    item_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_unfinished_item",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.item_refs, "ProductUnfinishedItemsCandidate.item_refs", required=True)


@dataclass(frozen=True)
class ProductQualityEvidenceIndex(ProductArtifactBase):
    object_ref: str = "evidence:l6_phase6_product_quality_index"
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase6_quality_evidence",))
    fabricated_evidence: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.evidence_refs, "ProductQualityEvidenceIndex.evidence_refs", required=True)
        ensure_bool(self.fabricated_evidence, "ProductQualityEvidenceIndex.fabricated_evidence")
        if self.fabricated_evidence:
            raise ValueError("ProductQualityEvidenceIndex cannot fabricate evidence")
