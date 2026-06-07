"""File action grounding request for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .adapter_envelope import AdapterInputEnvelope
from .external_action_envelope import FileActionEnvelope
from .external_action_risk_surface import ExternalActionRiskSurface
from .external_action_scope import ExternalActionScope
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true
from .permit_ref import ActionPermitRef
from .resource_usage_descriptor import ResourceUsageDescriptor
from .reversibility_descriptor import ReversibilityDescriptor
from .side_effect_descriptor import SideEffectDescriptor


@dataclass(frozen=True, slots=True)
class FileActionRequest:
    """LLM file-action intent carrier; it does not touch the local file system."""

    request_ref: TypedRef
    path_intent_ref: TypedRef
    operation_ref: TypedRef
    action_envelope: FileActionEnvelope
    scope: ExternalActionScope
    side_effect: SideEffectDescriptor
    reversibility: ReversibilityDescriptor
    resource_usage: ResourceUsageDescriptor
    risk_surface: ExternalActionRiskSurface
    parameter_envelope: AdapterInputEnvelope | None = None
    permit_ref: ActionPermitRef | None = None
    trace_ref: TypedRef | None = None
    l3_action_intent_ref: TypedRef | None = None
    l3_tool_intent_ref: TypedRef | None = None
    advisory_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    dry_run: bool = True
    production_path: bool = False
    request_only: bool = True
    reads_real_file: bool = False
    writes_real_file: bool = False
    deletes_real_file: bool = False
    overwrites_real_file: bool = False
    contains_plain_credential: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.request_only, "FileActionRequest.request_only")
        ensure_false(self.reads_real_file, "FileActionRequest.reads_real_file")
        ensure_false(self.writes_real_file, "FileActionRequest.writes_real_file")
        ensure_false(self.deletes_real_file, "FileActionRequest.deletes_real_file")
        ensure_false(self.overwrites_real_file, "FileActionRequest.overwrites_real_file")
        ensure_false(self.contains_plain_credential, "FileActionRequest.contains_plain_credential")
        ensure_false(self.writes_l2_state, "FileActionRequest.writes_l2_state")
        ensure_false(self.writes_audit_store, "FileActionRequest.writes_audit_store")
        ensure_schema_version(self.schema_version, "FileActionRequest.schema_version")
