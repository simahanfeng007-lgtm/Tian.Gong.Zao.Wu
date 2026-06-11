"""External action envelopes for file, network, terminal, and desktop surfaces."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .external_action_risk_surface import ExternalActionRiskSurface
from .external_action_scope import ExternalActionScope
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true
from .permit_ref import ActionPermitRef
from .resource_usage_descriptor import ResourceUsageDescriptor
from .reversibility_descriptor import ReversibilityDescriptor
from .side_effect_descriptor import SideEffectDescriptor


@dataclass(frozen=True, slots=True)
class ExternalActionEnvelope:
    """Shared envelope; it carries structure and never performs an action."""

    envelope_ref: TypedRef
    action_kind: str
    request_ref: TypedRef
    scope: ExternalActionScope
    side_effect: SideEffectDescriptor
    reversibility: ReversibilityDescriptor
    resource_usage: ResourceUsageDescriptor
    risk_surface: ExternalActionRiskSurface
    permit_ref: ActionPermitRef | None = None
    trace_ref: TypedRef | None = None
    communication_envelope_ref: TypedRef | None = None
    handoff_ref: TypedRef | None = None
    actor_ref: TypedRef | None = None
    conversation_ref: TypedRef | None = None
    authority_ref: TypedRef | None = None
    provenance_ref: TypedRef | None = None
    envelope_only: bool = True
    grants_permission: bool = False
    performs_action: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.action_kind, "ExternalActionEnvelope.action_kind", 128)
        ensure_true(self.envelope_only, "ExternalActionEnvelope.envelope_only")
        ensure_false(self.grants_permission, "ExternalActionEnvelope.grants_permission")
        ensure_false(self.performs_action, "ExternalActionEnvelope.performs_action")
        ensure_schema_version(self.schema_version, "ExternalActionEnvelope.schema_version")


@dataclass(frozen=True, slots=True)
class FileActionEnvelope:
    envelope_ref: TypedRef
    request_ref: TypedRef
    scope: ExternalActionScope
    side_effect: SideEffectDescriptor
    reversibility: ReversibilityDescriptor
    resource_usage: ResourceUsageDescriptor
    risk_surface: ExternalActionRiskSurface
    permit_ref: ActionPermitRef | None = None
    trace_ref: TypedRef | None = None
    communication_envelope_ref: TypedRef | None = None
    handoff_ref: TypedRef | None = None
    actor_ref: TypedRef | None = None
    conversation_ref: TypedRef | None = None
    action_kind: str = "file_action"
    envelope_only: bool = True
    grants_permission: bool = False
    performs_action: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.action_kind, "FileActionEnvelope.action_kind", 128)
        ensure_true(self.envelope_only, "FileActionEnvelope.envelope_only")
        ensure_false(self.grants_permission, "FileActionEnvelope.grants_permission")
        ensure_false(self.performs_action, "FileActionEnvelope.performs_action")
        ensure_schema_version(self.schema_version, "FileActionEnvelope.schema_version")


@dataclass(frozen=True, slots=True)
class NetworkActionEnvelope:
    envelope_ref: TypedRef
    request_ref: TypedRef
    scope: ExternalActionScope
    side_effect: SideEffectDescriptor
    reversibility: ReversibilityDescriptor
    resource_usage: ResourceUsageDescriptor
    risk_surface: ExternalActionRiskSurface
    permit_ref: ActionPermitRef | None = None
    trace_ref: TypedRef | None = None
    communication_envelope_ref: TypedRef | None = None
    handoff_ref: TypedRef | None = None
    actor_ref: TypedRef | None = None
    conversation_ref: TypedRef | None = None
    action_kind: str = "network_action"
    envelope_only: bool = True
    grants_permission: bool = False
    performs_action: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.action_kind, "NetworkActionEnvelope.action_kind", 128)
        ensure_true(self.envelope_only, "NetworkActionEnvelope.envelope_only")
        ensure_false(self.grants_permission, "NetworkActionEnvelope.grants_permission")
        ensure_false(self.performs_action, "NetworkActionEnvelope.performs_action")
        ensure_schema_version(self.schema_version, "NetworkActionEnvelope.schema_version")


@dataclass(frozen=True, slots=True)
class TerminalActionEnvelope:
    envelope_ref: TypedRef
    request_ref: TypedRef
    scope: ExternalActionScope
    side_effect: SideEffectDescriptor
    reversibility: ReversibilityDescriptor
    resource_usage: ResourceUsageDescriptor
    risk_surface: ExternalActionRiskSurface
    permit_ref: ActionPermitRef | None = None
    trace_ref: TypedRef | None = None
    communication_envelope_ref: TypedRef | None = None
    handoff_ref: TypedRef | None = None
    actor_ref: TypedRef | None = None
    conversation_ref: TypedRef | None = None
    action_kind: str = "terminal_action"
    envelope_only: bool = True
    grants_permission: bool = False
    performs_action: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.action_kind, "TerminalActionEnvelope.action_kind", 128)
        ensure_true(self.envelope_only, "TerminalActionEnvelope.envelope_only")
        ensure_false(self.grants_permission, "TerminalActionEnvelope.grants_permission")
        ensure_false(self.performs_action, "TerminalActionEnvelope.performs_action")
        ensure_schema_version(self.schema_version, "TerminalActionEnvelope.schema_version")


@dataclass(frozen=True, slots=True)
class DesktopActionEnvelope:
    envelope_ref: TypedRef
    request_ref: TypedRef
    scope: ExternalActionScope
    side_effect: SideEffectDescriptor
    reversibility: ReversibilityDescriptor
    resource_usage: ResourceUsageDescriptor
    risk_surface: ExternalActionRiskSurface
    permit_ref: ActionPermitRef | None = None
    trace_ref: TypedRef | None = None
    communication_envelope_ref: TypedRef | None = None
    handoff_ref: TypedRef | None = None
    actor_ref: TypedRef | None = None
    conversation_ref: TypedRef | None = None
    action_kind: str = "desktop_action"
    envelope_only: bool = True
    grants_permission: bool = False
    performs_action: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.action_kind, "DesktopActionEnvelope.action_kind", 128)
        ensure_true(self.envelope_only, "DesktopActionEnvelope.envelope_only")
        ensure_false(self.grants_permission, "DesktopActionEnvelope.grants_permission")
        ensure_false(self.performs_action, "DesktopActionEnvelope.performs_action")
        ensure_schema_version(self.schema_version, "DesktopActionEnvelope.schema_version")
