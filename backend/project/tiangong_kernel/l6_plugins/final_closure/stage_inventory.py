"""L6 phase8 stage inventory contracts."""
from __future__ import annotations
from dataclasses import dataclass, field
from .common import FinalClosureArtifactBase, ensure_non_negative_int

@dataclass(frozen=True)
class L6StageInventory(FinalClosureArtifactBase):
    object_ref: str = "l6:phase8_stage_inventory"
    phase_count: int = 7
    plugin_group_count: int = 7
    def __post_init__(self) -> None:
        super().__post_init__(); ensure_non_negative_int(self.phase_count, "phase_count"); ensure_non_negative_int(self.plugin_group_count, "plugin_group_count")
        if self.phase_count != 7: raise ValueError("L6 stage inventory must cover phase1 to phase7")

@dataclass(frozen=True)
class L6StageArtifactIndex(FinalClosureArtifactBase): object_ref: str = "l6:phase8_stage_artifact_index"
@dataclass(frozen=True)
class L6PluginGroupInventory(FinalClosureArtifactBase): object_ref: str = "l6:phase8_plugin_group_inventory"
@dataclass(frozen=True)
class L6ObjectInventory(FinalClosureArtifactBase): object_ref: str = "l6:phase8_object_inventory"
@dataclass(frozen=True)
class L6TestInventory(FinalClosureArtifactBase): object_ref: str = "l6:phase8_test_inventory"
@dataclass(frozen=True)
class L6ReportInventory(FinalClosureArtifactBase): object_ref: str = "l6:phase8_report_inventory"
@dataclass(frozen=True)
class L6QualityGateInventory(FinalClosureArtifactBase): object_ref: str = "l6:phase8_quality_gate_inventory"
@dataclass(frozen=True)
class L6RiskInventory(FinalClosureArtifactBase): object_ref: str = "l6:phase8_risk_inventory"
