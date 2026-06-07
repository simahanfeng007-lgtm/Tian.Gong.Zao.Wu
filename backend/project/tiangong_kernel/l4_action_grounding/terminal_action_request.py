"""Terminal action grounding request for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .external_action_envelope import TerminalActionEnvelope
from .external_action_risk_surface import ExternalActionRiskSurface
from .external_action_scope import ExternalActionScope
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true
from .permit_ref import ActionPermitRef
from .resource_usage_descriptor import ResourceUsageDescriptor
from .reversibility_descriptor import ReversibilityDescriptor
from .side_effect_descriptor import SideEffectDescriptor


@dataclass(frozen=True, slots=True)
class TerminalActionRequest:
    """LLM terminal-action intent carrier; it starts no process."""

    request_ref: TypedRef
    command_ref: TypedRef
    args_ref: TypedRef | None
    working_dir_ref: TypedRef | None
    env_ref: TypedRef | None
    action_envelope: TerminalActionEnvelope
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
    executes_real_command: bool = False
    reads_real_environment: bool = False
    starts_process: bool = False
    escalates_privilege: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.request_only, "TerminalActionRequest.request_only")
        ensure_false(self.executes_real_command, "TerminalActionRequest.executes_real_command")
        ensure_false(self.reads_real_environment, "TerminalActionRequest.reads_real_environment")
        ensure_false(self.starts_process, "TerminalActionRequest.starts_process")
        ensure_false(self.escalates_privilege, "TerminalActionRequest.escalates_privilege")
        ensure_false(self.writes_l2_state, "TerminalActionRequest.writes_l2_state")
        ensure_false(self.writes_audit_store, "TerminalActionRequest.writes_audit_store")
        ensure_schema_version(self.schema_version, "TerminalActionRequest.schema_version")
