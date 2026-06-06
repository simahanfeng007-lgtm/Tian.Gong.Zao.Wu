"""L4 动作落地会话对象。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true
from .status import ActionGroundingStatusKind


@dataclass(frozen=True, slots=True)
class ActionGroundingSession:
    """动作落地会话；聚合引用，不调度并发、不推进下一步。"""

    session_ref: TypedRef
    context_ref: TypedRef
    step_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    failure_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    gate_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    adapter_registry_snapshot_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    adapter_selection_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    adapter_output_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    adapter_failure_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    session_status: ActionGroundingStatusKind = ActionGroundingStatusKind.CREATED
    reason_summary: str = ""
    llm_controlled: bool = True
    l4_autonomous: bool = False
    session_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.reason_summary, "ActionGroundingSession.reason_summary")
        ensure_true(self.llm_controlled, "ActionGroundingSession.llm_controlled")
        ensure_false(self.l4_autonomous, "ActionGroundingSession.l4_autonomous")
        ensure_true(self.session_only, "ActionGroundingSession.session_only")
        ensure_schema_version(self.schema_version, "ActionGroundingSession.schema_version")
