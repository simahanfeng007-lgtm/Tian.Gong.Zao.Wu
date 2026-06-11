from __future__ import annotations
from dataclasses import dataclass
from .common import AdaptiveArtifactBase

@dataclass(frozen=True)
class ToolGapRequirement(AdaptiveArtifactBase):
    object_ref: str = "tool-cap:l6_phase7_tool_gap_requirement"
    produces_tool: bool = False
    releases_tool_handle: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.produces_tool or self.releases_tool_handle:
            raise ValueError("ToolGapRequirement is not tool production or handle release")

@dataclass(frozen=True)
class ToolCapabilityRequirement(AdaptiveArtifactBase):
    object_ref: str = "tool-cap:l6_phase7_tool_capability_requirement"
    calls_tool: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.calls_tool:
            raise ValueError("ToolCapabilityRequirement is not a tool call")

@dataclass(frozen=True)
class ToolProductionRequestCandidate(AdaptiveArtifactBase):
    object_ref: str = "request:l6_phase7_tool_production_candidate"
    produces_tool: bool = False

@dataclass(frozen=True)
class ToolSafetyRequirement(AdaptiveArtifactBase):
    object_ref: str = "requirement:l6_phase7_tool_safety"

@dataclass(frozen=True)
class ToolValidationRequirement(AdaptiveArtifactBase):
    object_ref: str = "validation:l6_phase7_tool_validation"

class ToolGapRequirementPlugin:
    declaration_ref = "decl:l6_phase7_tool_gap_requirement_plugin"
