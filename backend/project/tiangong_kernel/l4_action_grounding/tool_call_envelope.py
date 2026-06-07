"""Tool call envelope for L4 phase 4."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true
from .permit_ref import ActionPermitRef
from .tool_argument_envelope import ToolArgumentEnvelope


@dataclass(frozen=True, slots=True)
class ToolCallEnvelope:
    """One tool call structure; it does not expose or invoke a real tool."""

    call_ref: TypedRef
    tool_ref: TypedRef
    tool_group_ref: TypedRef | None = None
    action_intent_ref: TypedRef | None = None
    tool_intent_ref: TypedRef | None = None
    arguments_envelope: ToolArgumentEnvelope | None = None
    permit_ref: ActionPermitRef | None = None
    trace_ref: TypedRef | None = None
    communication_envelope_ref: TypedRef | None = None
    source_handoff_ref: TypedRef | None = None
    actor_ref: TypedRef | None = None
    conversation_ref: TypedRef | None = None
    authority_ref: TypedRef | None = None
    provenance_ref: TypedRef | None = None
    dry_run: bool = True
    production_path: bool = False
    call_envelope_only: bool = True
    l4_invokes_real_tool: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_false(self.l4_invokes_real_tool, "ToolCallEnvelope.l4_invokes_real_tool")
        ensure_true(self.call_envelope_only, "ToolCallEnvelope.call_envelope_only")
        ensure_schema_version(self.schema_version, "ToolCallEnvelope.schema_version")
