from __future__ import annotations
from dataclasses import dataclass
from .common import AdaptiveArtifactBase

@dataclass(frozen=True)
class RegressionValidationRequirement(AdaptiveArtifactBase):
    object_ref: str = "regression:l6_phase7_regression_validation_requirement"
    executes_pytest: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.executes_pytest:
            raise ValueError("RegressionValidationRequirement is not pytest execution")

@dataclass(frozen=True)
class TargetedTestRequirement(AdaptiveArtifactBase):
    object_ref: str = "test:l6_phase7_targeted_test_requirement"

@dataclass(frozen=True)
class FullPytestRequirement(AdaptiveArtifactBase):
    object_ref: str = "test:l6_phase7_full_pytest_requirement"
    full_pytest_passed: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.full_pytest_passed:
            raise ValueError("FullPytestRequirement cannot assert full pytest passed")

@dataclass(frozen=True)
class ForbiddenScanRequirement(AdaptiveArtifactBase):
    object_ref: str = "forbid:l6_phase7_forbidden_scan_requirement"

@dataclass(frozen=True)
class HashCompareRequirement(AdaptiveArtifactBase):
    object_ref: str = "test:l6_phase7_hash_compare_requirement"

@dataclass(frozen=True)
class TestInventoryCompareRequirement(AdaptiveArtifactBase):
    object_ref: str = "test:l6_phase7_test_inventory_compare_requirement"

@dataclass(frozen=True)
class PublicProjectionSafetyRequirement(AdaptiveArtifactBase):
    object_ref: str = "redaction:l6_phase7_public_projection_safety_requirement"

@dataclass(frozen=True)
class AuditEvidenceChainRequirement(AdaptiveArtifactBase):
    object_ref: str = "audit:l6_phase7_audit_evidence_chain_requirement"

class RegressionValidationRequirementPlugin:
    declaration_ref = "decl:l6_phase7_regression_validation_requirement_plugin"
