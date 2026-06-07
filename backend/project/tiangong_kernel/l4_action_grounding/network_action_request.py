"""Network action grounding request for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .external_action_envelope import NetworkActionEnvelope
from .external_action_risk_surface import ExternalActionRiskSurface
from .external_action_scope import ExternalActionScope
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true
from .permit_ref import ActionPermitRef
from .resource_usage_descriptor import ResourceUsageDescriptor
from .reversibility_descriptor import ReversibilityDescriptor
from .side_effect_descriptor import SideEffectDescriptor


@dataclass(frozen=True, slots=True)
class NetworkActionRequest:
    """LLM network-action intent carrier; it sends nothing."""

    request_ref: TypedRef
    url_ref: TypedRef
    method_ref: TypedRef
    payload_ref: TypedRef | None
    headers_ref: TypedRef | None
    action_envelope: NetworkActionEnvelope
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
    accesses_real_network: bool = False
    sends_real_payload: bool = False
    resolves_plain_credential: bool = False
    caches_real_response_body: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.request_only, "NetworkActionRequest.request_only")
        ensure_false(self.accesses_real_network, "NetworkActionRequest.accesses_real_network")
        ensure_false(self.sends_real_payload, "NetworkActionRequest.sends_real_payload")
        ensure_false(self.resolves_plain_credential, "NetworkActionRequest.resolves_plain_credential")
        ensure_false(self.caches_real_response_body, "NetworkActionRequest.caches_real_response_body")
        ensure_false(self.writes_l2_state, "NetworkActionRequest.writes_l2_state")
        ensure_false(self.writes_audit_store, "NetworkActionRequest.writes_audit_store")
        ensure_schema_version(self.schema_version, "NetworkActionRequest.schema_version")
