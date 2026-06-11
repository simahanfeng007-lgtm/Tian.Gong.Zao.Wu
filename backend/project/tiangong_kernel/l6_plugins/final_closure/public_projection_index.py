"""L6 phase8 public projection index contracts."""
from __future__ import annotations
from dataclasses import dataclass
from .common import FinalClosureArtifactBase

@dataclass(frozen=True)
class L6PublicProjectionIndex(FinalClosureArtifactBase):
    object_ref: str = "public:l6_phase8_projection_index"
    minimal_disclosure: bool = True
    contains_sensitive_detail: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.minimal_disclosure or self.contains_sensitive_detail: raise ValueError("Public projection index must be minimal disclosure only")
@dataclass(frozen=True)
class L6PublicProjectionSafetyReport(L6PublicProjectionIndex): object_ref: str = "report:l6_phase8_public_projection_safety"
@dataclass(frozen=True)
class L6SensitiveFieldRedactionReport(L6PublicProjectionIndex): object_ref: str = "redaction:l6_phase8_sensitive_field_report"
@dataclass(frozen=True)
class L6MinimalDisclosureReport(L6PublicProjectionIndex): object_ref: str = "report:l6_phase8_minimal_disclosure"
@dataclass(frozen=True)
class L6PublicProjectionLeakRiskSummary(L6PublicProjectionIndex): object_ref: str = "report:l6_phase8_public_leak_risk"
