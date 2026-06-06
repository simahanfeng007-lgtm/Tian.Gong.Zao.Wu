"""L3 第二阶段编排生命周期枚举与候选事实。

本模块只表达 Run / Task / Turn / Step 的流程状态建议。
它不推进状态、不写入 L2、不调用模型、不调用工具、不发起执行。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class OrchestrationLifecycleKind(str, Enum):
    """L3 第二阶段允许表达的流程生命周期。"""

    UNKNOWN = "unknown"
    CREATED = "created"
    PREPARED = "prepared"
    ACTIVE = "active"
    WAITING = "waiting"
    PAUSED = "paused"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    RESUMABLE = "resumable"
    ABANDONED = "abandoned"


class LifecycleTransitionIntent(str, Enum):
    """下一步流程意图；仅是建议，不是执行动作。"""

    UNKNOWN = "unknown"
    CONTINUE_CURRENT_STEP = "continue_current_step"
    ADVANCE_TO_NEXT_STEP = "advance_to_next_step"
    WAIT_FOR_MISSING_STATE = "wait_for_missing_state"
    PAUSE_AND_PRESERVE_CONTEXT = "pause_and_preserve_context"
    MARK_BLOCKED_FOR_REVIEW = "mark_blocked_for_review"
    SUGGEST_RESUME_PATH = "suggest_resume_path"
    SUGGEST_CANCEL_PATH = "suggest_cancel_path"
    SUGGEST_RECOVERY_PATH = "suggest_recovery_path"
    ABANDON_WITH_REASON = "abandon_with_reason"


@dataclass(frozen=True, slots=True)
class LifecycleTransitionCandidate:
    """生命周期转移候选事实。

    作用：表达当前生命周期、候选生命周期、意图、评分提示与证据引用。
    边界：不修改任何状态，不触发 L4/L5/L6，只供后续建议对象引用。
    """

    candidate_ref: TypedRef | None = None
    subject_ref: TypedRef | None = None
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    candidate_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    intent: LifecycleTransitionIntent = LifecycleTransitionIntent.UNKNOWN
    score_hint: float = 0.0
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_state_fields: tuple[str, ...] = field(default_factory=tuple)
    reason_items: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.score_hint <= 1.0:
            raise ValueError("LifecycleTransitionCandidate.score_hint must be between 0.0 and 1.0")
        if self.advisory_only is not True:
            raise ValueError("LifecycleTransitionCandidate.advisory_only must remain true in L3 phase 2")
        if any(len(item) > 128 for item in self.missing_state_fields):
            raise ValueError("LifecycleTransitionCandidate.missing_state_fields entries must be short")
        if any(len(item) > 256 for item in self.reason_items):
            raise ValueError("LifecycleTransitionCandidate.reason_items entries must be short")
        if not self.schema_version:
            raise ValueError("LifecycleTransitionCandidate.schema_version cannot be empty")
