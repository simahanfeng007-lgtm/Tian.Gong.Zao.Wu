"""L4 动作落地失败对象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .error import ActionGroundingError
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text


class ActionGroundingFailureKind(str, Enum):
    DISABLED_BY_DEFAULT = "disabled_by_default"
    BOUNDARY_PERMIT_REQUIRED = "boundary_permit_required"
    STRUCTURE_INVALID = "structure_invalid"
    REAL_ACTION_FORBIDDEN = "real_action_forbidden"


@dataclass(frozen=True, slots=True)
class ActionGroundingFailure:
    """标准失败 envelope；不执行重试、不写状态、不写审计。"""

    failure_ref: TypedRef
    failure_kind: ActionGroundingFailureKind = ActionGroundingFailureKind.DISABLED_BY_DEFAULT
    reason_summary: str = "missing future L5 permit; live action is disabled"
    source_request_ref: TypedRef | None = None
    permit_failure_ref: TypedRef | None = None
    boundary_feedback_ref: TypedRef | None = None
    adapter_failure_ref: TypedRef | None = None
    adapter_selection_result_ref: TypedRef | None = None
    error: ActionGroundingError | None = None
    blocked_invariant_names: tuple[str, ...] = field(default_factory=tuple)
    l5_permit_required: bool = True
    live_action_performed: bool = False
    retryable: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.reason_summary, "ActionGroundingFailure.reason_summary")
        for item in self.blocked_invariant_names:
            ensure_short_text(item, "ActionGroundingFailure.blocked_invariant_names", 128)
        ensure_false(self.live_action_performed, "ActionGroundingFailure.live_action_performed")
        ensure_false(self.retryable, "ActionGroundingFailure.retryable")
        ensure_schema_version(self.schema_version, "ActionGroundingFailure.schema_version")
