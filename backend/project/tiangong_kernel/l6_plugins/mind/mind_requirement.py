"""L6 phase3 mind requirement adapters.

Mind plugins may declare model/tool/governance needs, but every need remains a
requirement-only object for L3/L5 review.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version
from tiangong_kernel.l6_plugins.common.requirement import L6ModelCapabilityRequirement, L6ToolCapabilityRequirement


@dataclass(frozen=True)
class MindModelNeed:
    need_ref: str = "model-cap:l6_phase3_mind_model_need"
    source_plugin_ref: str = "mind:plugin"
    requirement: L6ModelCapabilityRequirement = field(default_factory=L6ModelCapabilityRequirement)
    requirement_only: bool = True
    calls_model: bool = False
    direct_l4_adapter_access: bool = False
    raw_http_allowed: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.need_ref, "MindModelNeed.need_ref")
        ensure_ref_text(self.source_plugin_ref, "MindModelNeed.source_plugin_ref")
        if not isinstance(self.requirement, L6ModelCapabilityRequirement):
            raise ValueError("MindModelNeed.requirement must be L6ModelCapabilityRequirement")
        for field_name in ("requirement_only", "calls_model", "direct_l4_adapter_access", "raw_http_allowed"):
            ensure_bool(getattr(self, field_name), f"MindModelNeed.{field_name}")
        if not self.requirement_only or self.calls_model or self.direct_l4_adapter_access or self.raw_http_allowed:
            raise ValueError("Mind model need can only output model requirement")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True)
class MindToolNeed:
    need_ref: str = "tool-cap:l6_phase3_mind_tool_need"
    source_plugin_ref: str = "mind:plugin"
    requirement: L6ToolCapabilityRequirement = field(default_factory=L6ToolCapabilityRequirement)
    requirement_only: bool = True
    invokes_tool: bool = False
    tool_refs: tuple[str, ...] = field(default_factory=lambda: ("tool-cap:l6_mind_required_tool",))
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.need_ref, "MindToolNeed.need_ref")
        ensure_ref_text(self.source_plugin_ref, "MindToolNeed.source_plugin_ref")
        if not isinstance(self.requirement, L6ToolCapabilityRequirement):
            raise ValueError("MindToolNeed.requirement must be L6ToolCapabilityRequirement")
        ensure_ref_items(self.tool_refs, "MindToolNeed.tool_refs", required=True)
        for field_name in ("requirement_only", "invokes_tool"):
            ensure_bool(getattr(self, field_name), f"MindToolNeed.{field_name}")
        if not self.requirement_only or self.invokes_tool:
            raise ValueError("Mind tool need can only output tool requirement")
        ensure_schema_version(self.schema_version)
