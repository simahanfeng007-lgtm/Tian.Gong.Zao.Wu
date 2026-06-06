"""Communication and handoff bindings for L4 action grounding."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class CommunicationEnvelopeBinding:
    binding_ref: TypedRef
    communication_envelope_ref: TypedRef
    source_actor_ref: TypedRef | None = None
    target_actor_ref: TypedRef | None = None
    conversation_ref: TypedRef | None = None
    authority_ref: TypedRef | None = None
    provenance_ref: TypedRef | None = None
    ref_only: bool = True
    escalates_authority: bool = False
    sends_message: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "CommunicationEnvelopeBinding.ref_only")
        ensure_false(self.escalates_authority, "CommunicationEnvelopeBinding.escalates_authority")
        ensure_false(self.sends_message, "CommunicationEnvelopeBinding.sends_message")
        ensure_schema_version(self.schema_version, "CommunicationEnvelopeBinding.schema_version")


@dataclass(frozen=True, slots=True)
class HandoffActionBinding:
    binding_ref: TypedRef
    source_handoff_ref: TypedRef
    communication_envelope_ref: TypedRef
    parent_run_ref: TypedRef | None = None
    parent_task_ref: TypedRef | None = None
    from_actor_ref: TypedRef | None = None
    to_actor_ref: TypedRef | None = None
    conversation_ref: TypedRef | None = None
    authority_ref: TypedRef | None = None
    provenance_ref: TypedRef | None = None
    binding_only: bool = True
    executes_handoff: bool = False
    grants_authority: bool = False
    shares_raw_tool_handle: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.binding_only, "HandoffActionBinding.binding_only")
        ensure_false(self.executes_handoff, "HandoffActionBinding.executes_handoff")
        ensure_false(self.grants_authority, "HandoffActionBinding.grants_authority")
        ensure_false(self.shares_raw_tool_handle, "HandoffActionBinding.shares_raw_tool_handle")
        ensure_schema_version(self.schema_version, "HandoffActionBinding.schema_version")


@dataclass(frozen=True, slots=True)
class HandoffReturnBinding:
    binding_ref: TypedRef
    source_handoff_ref: TypedRef
    conversation_ref: TypedRef | None = None
    parent_run_ref: TypedRef | None = None
    parent_task_ref: TypedRef | None = None
    result_ref: TypedRef | None = None
    failure_ref: TypedRef | None = None
    observation_ref: TypedRef | None = None
    binding_only: bool = True
    writes_parent_state: bool = False
    decides_next_step: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.binding_only, "HandoffReturnBinding.binding_only")
        ensure_false(self.writes_parent_state, "HandoffReturnBinding.writes_parent_state")
        ensure_false(self.decides_next_step, "HandoffReturnBinding.decides_next_step")
        ensure_schema_version(self.schema_version, "HandoffReturnBinding.schema_version")
