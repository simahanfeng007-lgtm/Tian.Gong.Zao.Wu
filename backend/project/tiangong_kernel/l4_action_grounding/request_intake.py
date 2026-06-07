"""L4 接收 L3 执行请求的结构对象。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l3_orchestration.execution_request import (
    ExecutionDispatchRequest,
    ExecutionPlanRef,
    ExecutionRequest,
    ExecutionStepRef,
)

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ActionRequestIntake:
    """L3 请求接收对象；不修改 L3，不派发真实动作。"""

    intake_ref: TypedRef
    execution_request: ExecutionRequest | None = None
    dispatch_request: ExecutionDispatchRequest | None = None
    execution_request_ref: TypedRef | None = None
    execution_plan_ref: ExecutionPlanRef | None = None
    execution_step_refs: tuple[ExecutionStepRef, ...] = field(default_factory=tuple)
    source_handoff_ref: TypedRef | None = None
    l5_permit_ref: TypedRef | None = None
    request_structure_complete: bool = True
    intake_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.execution_request is None and self.dispatch_request is None and self.execution_request_ref is None:
            raise ValueError("ActionRequestIntake requires an L3 execution request object or ref")
        if self.execution_request is not None:
            ensure_true(self.execution_request.request_only, "ExecutionRequest.request_only")
        if self.dispatch_request is not None:
            ensure_true(self.dispatch_request.request_only, "ExecutionDispatchRequest.request_only")
        ensure_true(self.intake_only, "ActionRequestIntake.intake_only")
        ensure_schema_version(self.schema_version, "ActionRequestIntake.schema_version")

    @property
    def source_request_ref(self) -> TypedRef | None:
        if self.execution_request_ref is not None:
            return self.execution_request_ref
        if self.execution_request is not None:
            return self.execution_request.request_ref.request_ref
        if self.dispatch_request is not None:
            return self.dispatch_request.request_ref.request_ref
        return None

    @property
    def has_l5_permit_ref(self) -> bool:
        """只表示许可引用存在，不表达许可有效或可放行。"""

        return self.l5_permit_ref is not None


@dataclass(frozen=True, slots=True)
class ActionRequestIntakeSummary:
    """接收摘要；用于报告结构完整性，不做裁决。"""

    summary_ref: TypedRef
    intake_ref: TypedRef
    accepted_l3_object_names: tuple[str, ...] = ("ExecutionRequest", "ExecutionDispatchRequest", "ExecutionPlanRef", "ExecutionStepRef")
    missing_field_names: tuple[str, ...] = field(default_factory=tuple)
    summary: str = "L3 execution request refs are carried by L4 action grounding."
    summary_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.accepted_l3_object_names + self.missing_field_names:
            ensure_short_text(item, "ActionRequestIntakeSummary names", 128)
        ensure_short_text(self.summary, "ActionRequestIntakeSummary.summary")
        ensure_true(self.summary_only, "ActionRequestIntakeSummary.summary_only")
        ensure_schema_version(self.schema_version, "ActionRequestIntakeSummary.schema_version")
