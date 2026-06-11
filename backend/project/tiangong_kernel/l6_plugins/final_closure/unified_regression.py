"""L6 phase8 unified regression evidence contracts."""
from __future__ import annotations
from dataclasses import dataclass
from .common import FinalClosureArtifactBase

@dataclass(frozen=True)
class L6UnifiedHashCompareReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_hash_compare"
@dataclass(frozen=True)
class L6UnifiedTestInventoryCompareReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_test_inventory_compare"
@dataclass(frozen=True)
class L6UnifiedRegressionMatrix(FinalClosureArtifactBase): object_ref: str = "regression:l6_phase8_unified_matrix"
@dataclass(frozen=True)
class L6FullPytestEvidenceRef(FinalClosureArtifactBase):
    object_ref: str = "test:l6_phase8_full_pytest_evidence"
    result_ref: str = "test:l6_phase8_full_pytest_result"
    faked: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.faked: raise ValueError("full pytest evidence must not be faked")
@dataclass(frozen=True)
class L6ZipIntegrityReport(FinalClosureArtifactBase): object_ref: str = "report:l6_phase8_zip_integrity"
