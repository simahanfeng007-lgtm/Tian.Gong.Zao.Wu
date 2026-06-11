"""L4 动作落地上下文。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ActionGroundingContext:
    """动作落地上下文；第一阶段不绑定真实适配器。"""

    context_ref: TypedRef
    identity_ref: TypedRef
    intake_ref: TypedRef
    status_ref: TypedRef | None = None
    adapter_kind_hint: str = "no_live_adapter_bound"
    adapter_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    adapter_descriptor_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    adapter_registry_ref: TypedRef | None = None
    adapter_selection_ref: TypedRef | None = None
    l5_permit_ref: TypedRef | None = None
    boundary_decision_ref: TypedRef | None = None
    policy_decision_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    resource_limit_ref: TypedRef | None = None
    llm_controlled: bool = True
    l4_autonomous: bool = False
    live_action_enabled: bool = False
    context_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.adapter_kind_hint, "ActionGroundingContext.adapter_kind_hint", 128)
        ensure_true(self.llm_controlled, "ActionGroundingContext.llm_controlled")
        ensure_false(self.l4_autonomous, "ActionGroundingContext.l4_autonomous")
        ensure_false(self.live_action_enabled, "ActionGroundingContext.live_action_enabled")
        ensure_true(self.context_only, "ActionGroundingContext.context_only")
        ensure_schema_version(self.schema_version, "ActionGroundingContext.schema_version")
