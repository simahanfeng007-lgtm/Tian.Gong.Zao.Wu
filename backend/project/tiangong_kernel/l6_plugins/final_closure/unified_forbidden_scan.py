"""L6 phase8 unified forbidden scan contracts."""
from __future__ import annotations
from dataclasses import dataclass, field
from .common import FinalClosureArtifactBase

@dataclass(frozen=True)
class L6UnifiedForbiddenScanRuleSet(FinalClosureArtifactBase):
    object_ref: str = "forbid:l6_phase8_unified_rule_set"
    scan_scope_refs: tuple[str, ...] = field(default_factory=lambda: tuple(f"l6:phase{i}_scan_scope" for i in range(1, 9)))
    inert_pattern_only: bool = True
    def __post_init__(self) -> None:
        super().__post_init__()
        if len(self.scan_scope_refs) < 8 or not self.inert_pattern_only: raise ValueError("Unified forbidden scan must cover phase1 to phase8 inertly")

@dataclass(frozen=True)
class L6UnifiedForbiddenScanReport(FinalClosureArtifactBase):
    object_ref: str = "report:l6_phase8_unified_forbidden_scan"
    actionable_findings: int = 0
    p0_findings: int = 0
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.actionable_findings or self.p0_findings: raise ValueError("Unified forbidden scan blocks actionable findings")
