"""ToolGroup action context for L4 phase 4."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class ToolGroupActionContext:
    """ToolGroup release context references; no Skill or Tool registry lookup."""

    context_ref: TypedRef
    tool_group_ref: TypedRef
    skill_ref: TypedRef | None = None
    intent_ref: TypedRef | None = None
    available_tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    release_scope_ref: TypedRef | None = None
    l3_release_advice_ref: TypedRef | None = None
    l5_review_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    context_only: bool = True
    resolves_skill: bool = False
    registers_tool: bool = False
    grants_tool_permission: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.context_only, "ToolGroupActionContext.context_only")
        ensure_false(self.resolves_skill, "ToolGroupActionContext.resolves_skill")
        ensure_false(self.registers_tool, "ToolGroupActionContext.registers_tool")
        ensure_false(self.grants_tool_permission, "ToolGroupActionContext.grants_tool_permission")
        ensure_schema_version(self.schema_version, "ToolGroupActionContext.schema_version")
