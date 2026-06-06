"""L4 Context / Belief / World 安全投影。

投影默认把工具、模型和观察输出当作非指令数据，只携带引用，不保存明文输出。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ContextSafetyProjection:
    """L4 上下文安全投影。"""

    projection_ref: TypedRef
    source_ref: TypedRef | None = None
    source_trust_boundary_ref: TypedRef | None = None
    privacy_ref: TypedRef | None = None
    taint_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    observation_ref: TypedRef | None = None
    untrusted_output: bool = True
    instruction_eligible: bool = False
    system_instruction_eligible: bool = False
    context_injection_allowed: bool = False
    requires_l5_boundary_review: bool = True
    requires_l6_context_assembler: bool = True
    l4_writes_l2: bool = False
    l4_decides_context_injection: bool = False
    l4_updates_belief_state: bool = False
    l4_updates_world_state: bool = False
    stores_plain_output: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.untrusted_output, "L4ContextSafetyProjection.untrusted_output")
        ensure_false(self.instruction_eligible, "L4ContextSafetyProjection.instruction_eligible")
        ensure_false(self.system_instruction_eligible, "L4ContextSafetyProjection.system_instruction_eligible")
        ensure_false(self.context_injection_allowed, "L4ContextSafetyProjection.context_injection_allowed")
        ensure_true(self.requires_l5_boundary_review, "L4ContextSafetyProjection.requires_l5_boundary_review")
        ensure_true(self.requires_l6_context_assembler, "L4ContextSafetyProjection.requires_l6_context_assembler")
        ensure_false(self.l4_writes_l2, "L4ContextSafetyProjection.l4_writes_l2")
        ensure_false(self.l4_decides_context_injection, "L4ContextSafetyProjection.l4_decides_context_injection")
        ensure_false(self.l4_updates_belief_state, "L4ContextSafetyProjection.l4_updates_belief_state")
        ensure_false(self.l4_updates_world_state, "L4ContextSafetyProjection.l4_updates_world_state")
        ensure_false(self.stores_plain_output, "L4ContextSafetyProjection.stores_plain_output")
        ensure_schema_version(self.schema_version, "L4ContextSafetyProjection.schema_version")


@dataclass(frozen=True, slots=True)
class L4ToolOutputContextProjection(L4ContextSafetyProjection):
    """L4 工具输出上下文投影。"""

    tool_result_ref: TypedRef | None = None
    real_tool_called: bool = False

    def __post_init__(self) -> None:
        L4ContextSafetyProjection.__post_init__(self)
        ensure_false(self.real_tool_called, "L4ToolOutputContextProjection.real_tool_called")


@dataclass(frozen=True, slots=True)
class L4ModelOutputContextProjection(L4ContextSafetyProjection):
    """L4 模型输出上下文投影。"""

    model_result_ref: TypedRef | None = None
    real_model_called: bool = False

    def __post_init__(self) -> None:
        L4ContextSafetyProjection.__post_init__(self)
        ensure_false(self.real_model_called, "L4ModelOutputContextProjection.real_model_called")


@dataclass(frozen=True, slots=True)
class L4ObservationBeliefWorldProjection(L4ContextSafetyProjection):
    """L4 观察到信念/世界候选投影。"""

    belief_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    world_state_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    updates_belief_state: bool = False
    updates_world_state: bool = False

    def __post_init__(self) -> None:
        L4ContextSafetyProjection.__post_init__(self)
        ensure_false(self.updates_belief_state, "L4ObservationBeliefWorldProjection.updates_belief_state")
        ensure_false(self.updates_world_state, "L4ObservationBeliefWorldProjection.updates_world_state")
