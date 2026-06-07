from __future__ import annotations
from dataclasses import dataclass
from .common import AdaptiveArtifactBase

@dataclass(frozen=True)
class RepairPlanCandidate(AdaptiveArtifactBase):
    object_ref: str = "healing:l6_phase7_repair_plan_candidate"
    patches_code: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.patches_code:
            raise ValueError("RepairPlanCandidate is not a code patch")

@dataclass(frozen=True)
class FilePatchRequirement(AdaptiveArtifactBase):
    object_ref: str = "requirement:l6_phase7_file_patch"
    writes_file: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.writes_file:
            raise ValueError("FilePatchRequirement is not a file write")

@dataclass(frozen=True)
class TestRunRequirement(AdaptiveArtifactBase):
    __test__ = False
    object_ref: str = "test:l6_phase7_test_run_requirement"
    runs_tests: bool = False
    tests_passed: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.runs_tests or self.tests_passed:
            raise ValueError("TestRunRequirement is not test execution or a result")

@dataclass(frozen=True)
class RepairImpactScopeCandidate(AdaptiveArtifactBase):
    object_ref: str = "report:l6_phase7_repair_impact_scope"

@dataclass(frozen=True)
class RepairRollbackSuggestion(AdaptiveArtifactBase):
    object_ref: str = "suggestion:l6_phase7_repair_rollback"

@dataclass(frozen=True)
class RepairValidationRequirement(AdaptiveArtifactBase):
    object_ref: str = "validation:l6_phase7_repair_validation"

class RepairPlanCandidatePlugin:
    declaration_ref = "decl:l6_phase7_repair_plan_candidate_plugin"
