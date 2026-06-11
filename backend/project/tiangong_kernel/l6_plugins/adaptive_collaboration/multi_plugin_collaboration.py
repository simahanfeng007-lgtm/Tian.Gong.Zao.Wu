from __future__ import annotations
from dataclasses import dataclass, field
from .common import AdaptiveArtifactBase

@dataclass(frozen=True)
class MultiPluginCollaborationPlanCandidate(AdaptiveArtifactBase):
    object_ref: str = "handoff:l6_phase7_multi_plugin_collaboration_plan_candidate"
    dispatches_plugins: bool = False
    direct_plugin_call: bool = False
    host_mediated_only: bool = True
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.dispatches_plugins or self.direct_plugin_call or not self.host_mediated_only:
            raise ValueError("MultiPluginCollaborationPlanCandidate is not plugin dispatch or direct call")

@dataclass(frozen=True)
class PluginRoleAssignmentCandidate(AdaptiveArtifactBase):
    object_ref: str = "handoff:l6_phase7_plugin_role_assignment"

@dataclass(frozen=True)
class CollaborationInputOutputMap(AdaptiveArtifactBase):
    object_ref: str = "handoff:l6_phase7_collaboration_io_map"

@dataclass(frozen=True)
class CollaborationHandoffRoute(AdaptiveArtifactBase):
    object_ref: str = "handoff:l6_phase7_collaboration_handoff_route"

@dataclass(frozen=True)
class CollaborationRiskHint(AdaptiveArtifactBase):
    object_ref: str = "hint:l6_phase7_collaboration_risk"

@dataclass(frozen=True)
class CollaborationQualityRequirement(AdaptiveArtifactBase):
    object_ref: str = "requirement:l6_phase7_collaboration_quality"

class MultiPluginCollaborationPlanPlugin:
    declaration_ref = "decl:l6_phase7_multi_plugin_collaboration_plan_plugin"
