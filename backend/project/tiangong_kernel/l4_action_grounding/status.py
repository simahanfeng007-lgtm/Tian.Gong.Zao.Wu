"""L4 动作落地状态对象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text


class ActionGroundingMode(str, Enum):
    DISABLED_BY_DEFAULT = "disabled_by_default"
    FAKE = "fake"
    DRY_RUN = "dry_run"
    NO_OP = "no_op"


class ActionGroundingStatusKind(str, Enum):
    CREATED = "created"
    INTAKEN = "intaken"
    REJECTED = "rejected"
    SIMULATED = "simulated"
    DRY_RUN_RECORDED = "dry_run_recorded"
    NO_OP_RECORDED = "no_op_recorded"


@dataclass(frozen=True, slots=True)
class ActionGroundingStatus:
    """L4 状态事实；第一阶段不可启用真实动作。"""

    status_ref: TypedRef
    status_kind: ActionGroundingStatusKind = ActionGroundingStatusKind.CREATED
    mode: ActionGroundingMode = ActionGroundingMode.DISABLED_BY_DEFAULT
    reason_summary: str = ""
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l5_permit_ref: TypedRef | None = None
    ready_for_live_action: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.reason_summary, "ActionGroundingStatus.reason_summary")
        ensure_false(self.ready_for_live_action, "ActionGroundingStatus.ready_for_live_action")
        ensure_schema_version(self.schema_version, "ActionGroundingStatus.schema_version")
