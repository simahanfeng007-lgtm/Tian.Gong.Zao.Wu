"""L4 动作落地投影对象。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ActionGroundingProjection:
    """动作落地投影；只提供结果、失败和边界需求引用，不写 L2 状态。"""

    projection_ref: TypedRef
    intake_ref: TypedRef
    result_ref: TypedRef | None = None
    failure_ref: TypedRef | None = None
    adapter_projection_ref: TypedRef | None = None
    adapter_registry_projection_ref: TypedRef | None = None
    l3_request_ref: TypedRef | None = None
    l5_permit_required: bool = True
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    projection_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            ensure_short_text(item, "ActionGroundingProjection.reason_codes", 128)
        ensure_true(self.l5_permit_required, "ActionGroundingProjection.l5_permit_required")
        ensure_true(self.projection_only, "ActionGroundingProjection.projection_only")
        ensure_schema_version(self.schema_version, "ActionGroundingProjection.schema_version")
