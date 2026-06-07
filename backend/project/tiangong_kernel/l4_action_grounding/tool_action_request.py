"""Tool action request objects for L4 phase 4."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true
from .permit_ref import ActionPermitRef
from .tool_argument_envelope import ToolArgumentEnvelope
from .tool_call_envelope import ToolCallEnvelope
from .tool_group_action_context import ToolGroupActionContext


@dataclass(frozen=True, slots=True)
class ToolActionRequest:
    """Structure for an LLM tool-call intent grounding request."""

    request_ref: TypedRef
    tool_ref: TypedRef
    tool_group_ref: TypedRef
    arguments_envelope: ToolArgumentEnvelope
    tool_call_envelope: ToolCallEnvelope | None = None
    tool_group_context: ToolGroupActionContext | None = None
    permit_ref: ActionPermitRef | None = None
    execution_context_ref: TypedRef | None = None
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
    l3_tool_intent_ref: TypedRef | None = None
    l3_action_intent_ref: TypedRef | None = None
    advisory_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    dry_run: bool = True
    production_path: bool = False
    request_only: bool = True
    resolves_tool_registry: bool = False
    exposes_tool_to_model: bool = False
    real_tool_called: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.request_only, "ToolActionRequest.request_only")
        ensure_false(self.resolves_tool_registry, "ToolActionRequest.resolves_tool_registry")
        ensure_false(self.exposes_tool_to_model, "ToolActionRequest.exposes_tool_to_model")
        ensure_false(self.real_tool_called, "ToolActionRequest.real_tool_called")
        ensure_schema_version(self.schema_version, "ToolActionRequest.schema_version")

    @property
    def has_structured_resource_cost_refs(self) -> bool:
        return all(ref is not None for ref in (self.resource_usage, self.resource_budget_ref, self.cost_estimate_ref))
