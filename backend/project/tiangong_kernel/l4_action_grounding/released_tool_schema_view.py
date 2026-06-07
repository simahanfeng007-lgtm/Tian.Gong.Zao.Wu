"""L4 released tool schema read-only views.

These views describe model-visible tool schema references after future Skill
and ToolGroup release checks.  They never hold a real tool object and never
call a model or tool.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ReleasedToolSchemaView:
    """已释放工具 schema 只读视图，只保存引用。"""

    schema_view_ref: TypedRef | None = None
    skill_ref: TypedRef | None = None
    tool_group_ref: TypedRef | None = None
    release_ref: TypedRef | None = None
    tool_schema_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    permit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trace_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    visibility_reason_codes: tuple[str, ...] = field(default_factory=tuple)
    view_only: bool = True
    reference_only: bool = True
    model_visible: bool = True
    contains_real_tool_handle: bool = False
    registers_tool: bool = False
    calls_model_or_tool: bool = False
    signs_permit: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.visibility_reason_codes:
            ensure_short_text(item, "ReleasedToolSchemaView.visibility_reason_codes", 128)
        ensure_true(self.view_only, "ReleasedToolSchemaView.view_only")
        ensure_true(self.reference_only, "ReleasedToolSchemaView.reference_only")
        ensure_true(self.model_visible, "ReleasedToolSchemaView.model_visible")
        ensure_false(self.contains_real_tool_handle, "ReleasedToolSchemaView.contains_real_tool_handle")
        ensure_false(self.registers_tool, "ReleasedToolSchemaView.registers_tool")
        ensure_false(self.calls_model_or_tool, "ReleasedToolSchemaView.calls_model_or_tool")
        ensure_false(self.signs_permit, "ReleasedToolSchemaView.signs_permit")
        ensure_schema_version(self.schema_version, "ReleasedToolSchemaView.schema_version")


@dataclass(frozen=True, slots=True)
class ModelVisibleReleasedToolView:
    """模型可见工具视图，只承载 schema 与边界引用。"""

    view_ref: TypedRef | None = None
    released_schema_view_ref: TypedRef | None = None
    model_context_ref: TypedRef | None = None
    visible_tool_schema_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l5_review_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trace_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    model_visible: bool = True
    view_only: bool = True
    reference_only: bool = True
    contains_real_tool_handle: bool = False
    calls_model_or_tool: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.model_visible, "ModelVisibleReleasedToolView.model_visible")
        ensure_true(self.view_only, "ModelVisibleReleasedToolView.view_only")
        ensure_true(self.reference_only, "ModelVisibleReleasedToolView.reference_only")
        ensure_false(self.contains_real_tool_handle, "ModelVisibleReleasedToolView.contains_real_tool_handle")
        ensure_false(self.calls_model_or_tool, "ModelVisibleReleasedToolView.calls_model_or_tool")
        ensure_schema_version(self.schema_version, "ModelVisibleReleasedToolView.schema_version")
