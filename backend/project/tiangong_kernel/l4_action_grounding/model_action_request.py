"""Model action request objects for L4 phase 4."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .adapter_envelope import AdapterInputEnvelope
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true
from .permit_ref import ActionPermitRef


@dataclass(frozen=True, slots=True)
class ModelActionRequest:
    """Structure for a model action grounding request; no model client is held."""

    request_ref: TypedRef
    model_target_ref: TypedRef
    prompt_or_message_ref: TypedRef
    input_envelope: AdapterInputEnvelope
    execution_context_ref: TypedRef | None = None
    permit_ref: ActionPermitRef | None = None
    trace_ref: TypedRef | None = None
    resource_usage: TypedRef | None = None
    resource_budget_ref: TypedRef | None = None
    cost_estimate_ref: TypedRef | None = None
    quota_ref: TypedRef | None = None
    rate_limit_ref: TypedRef | None = None
    data_governance_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    privacy_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    disclosure_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trust_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l3_model_intent_ref: TypedRef | None = None
    l3_action_intent_ref: TypedRef | None = None
    advisory_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    dry_run: bool = True
    production_path: bool = False
    request_only: bool = True
    contains_plain_credential: bool = False
    has_real_model_client: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.request_only, "ModelActionRequest.request_only")
        ensure_false(self.contains_plain_credential, "ModelActionRequest.contains_plain_credential")
        ensure_false(self.has_real_model_client, "ModelActionRequest.has_real_model_client")
        ensure_schema_version(self.schema_version, "ModelActionRequest.schema_version")

    @property
    def has_structured_resource_cost_refs(self) -> bool:
        return all(ref is not None for ref in (self.resource_usage, self.resource_budget_ref, self.cost_estimate_ref))
