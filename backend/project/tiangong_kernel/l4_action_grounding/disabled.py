"""L4 第一阶段安全默认拒绝对象。"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .error import ActionGroundingError, ActionGroundingErrorKind
from .failure import ActionGroundingFailure, ActionGroundingFailureKind
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text


DEFAULT_DISABLED_REASON = "missing future L5 permit; L4 phase 1 refuses live action"


@dataclass(frozen=True, slots=True)
class ExecutionDisabledByDefaultFailure:
    """缺少未来 L5 许可时的稳定拒绝对象。"""

    failure_ref: TypedRef
    source_request_ref: TypedRef | None = None
    reason_summary: str = DEFAULT_DISABLED_REASON
    required_invariant_names: tuple[str, ...] = (
        "BoundaryPermitRequiredInvariant",
        "NoLiveExecutionWithoutL5Invariant",
    )
    l5_permit_required: bool = True
    live_action_performed: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.reason_summary, "ExecutionDisabledByDefaultFailure.reason_summary")
        for item in self.required_invariant_names:
            ensure_short_text(item, "ExecutionDisabledByDefaultFailure.required_invariant_names", 128)
        ensure_false(self.live_action_performed, "ExecutionDisabledByDefaultFailure.live_action_performed")
        ensure_schema_version(self.schema_version, "ExecutionDisabledByDefaultFailure.schema_version")

    def to_failure(self) -> ActionGroundingFailure:
        """转为通用失败 envelope；不产生任何副作用。"""

        return ActionGroundingFailure(
            failure_ref=self.failure_ref,
            failure_kind=ActionGroundingFailureKind.BOUNDARY_PERMIT_REQUIRED,
            reason_summary=self.reason_summary,
            source_request_ref=self.source_request_ref,
            error=ActionGroundingError(error_kind=ActionGroundingErrorKind.PERMIT_REQUIRED, message=self.reason_summary),
            blocked_invariant_names=self.required_invariant_names,
            l5_permit_required=self.l5_permit_required,
            live_action_performed=self.live_action_performed,
        )
