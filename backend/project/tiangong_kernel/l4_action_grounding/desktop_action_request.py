"""Desktop action grounding request for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .external_action_envelope import DesktopActionEnvelope
from .external_action_risk_surface import ExternalActionRiskSurface
from .external_action_scope import ExternalActionScope
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true
from .permit_ref import ActionPermitRef
from .resource_usage_descriptor import ResourceUsageDescriptor
from .reversibility_descriptor import ReversibilityDescriptor
from .side_effect_descriptor import SideEffectDescriptor


@dataclass(frozen=True, slots=True)
class DesktopActionRequest:
    """LLM desktop-action intent carrier; it controls no real UI."""

    request_ref: TypedRef
    ui_target_ref: TypedRef
    gesture_ref: TypedRef | None
    screen_region_ref: TypedRef | None
    input_ref: TypedRef | None
    action_envelope: DesktopActionEnvelope
    scope: ExternalActionScope
    side_effect: SideEffectDescriptor
    reversibility: ReversibilityDescriptor
    resource_usage: ResourceUsageDescriptor
    risk_surface: ExternalActionRiskSurface
    permit_ref: ActionPermitRef | None = None
    trace_ref: TypedRef | None = None
    l3_action_intent_ref: TypedRef | None = None
    l3_tool_intent_ref: TypedRef | None = None
    advisory_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    dry_run: bool = True
    production_path: bool = False
    request_only: bool = True
    clicks_real_ui: bool = False
    types_real_input: bool = False
    reads_real_screen: bool = False
    controls_real_window: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.request_only, "DesktopActionRequest.request_only")
        ensure_false(self.clicks_real_ui, "DesktopActionRequest.clicks_real_ui")
        ensure_false(self.types_real_input, "DesktopActionRequest.types_real_input")
        ensure_false(self.reads_real_screen, "DesktopActionRequest.reads_real_screen")
        ensure_false(self.controls_real_window, "DesktopActionRequest.controls_real_window")
        ensure_false(self.writes_l2_state, "DesktopActionRequest.writes_l2_state")
        ensure_false(self.writes_audit_store, "DesktopActionRequest.writes_audit_store")
        ensure_schema_version(self.schema_version, "DesktopActionRequest.schema_version")
