from __future__ import annotations
from dataclasses import dataclass
from .common import AdaptiveArtifactBase

@dataclass(frozen=True)
class SelfHealingDiagnosisCandidate(AdaptiveArtifactBase):
    object_ref: str = "healing:l6_phase7_self_healing_diagnosis_candidate"
    executes_healing: bool = False
    performs_rollback: bool = False
    performs_hot_switch: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.executes_healing or self.performs_rollback or self.performs_hot_switch:
            raise ValueError("SelfHealingDiagnosisCandidate is not healing execution")

@dataclass(frozen=True)
class FailureRootCauseCandidate(AdaptiveArtifactBase):
    object_ref: str = "healing:l6_phase7_failure_root_cause_candidate"

@dataclass(frozen=True)
class HealingNeedProjection(AdaptiveArtifactBase):
    object_ref: str = "projection:l6_phase7_healing_need"

@dataclass(frozen=True)
class HealingRiskHint(AdaptiveArtifactBase):
    object_ref: str = "hint:l6_phase7_healing_risk"

@dataclass(frozen=True)
class SelfHealingReentryRequest(AdaptiveArtifactBase):
    object_ref: str = "request:l6_phase7_self_healing_reentry"

class SelfHealingDiagnosisPlugin:
    declaration_ref = "decl:l6_phase7_self_healing_diagnosis_plugin"
