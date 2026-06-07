"""L3 第二阶段流程状态转移建议对象。

本模块只生成建议、阻断说明、L2 状态更新建议引用和未来层引用位，不执行转移。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l2_state.state_status import L2StateStatusKind

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionCandidate, LifecycleTransitionIntent, OrchestrationLifecycleKind


class StateUpdateSuggestionKind(str, Enum):
    """L2 状态更新建议类别；不是 L2 写入。"""

    UNKNOWN = "unknown"
    RECORD_LIFECYCLE_HINT = "record_lifecycle_hint"
    RECORD_PROGRESS_HINT = "record_progress_hint"
    RECORD_BLOCKER_HINT = "record_blocker_hint"
    RECORD_RESUME_HINT = "record_resume_hint"
    RECORD_CANCELLATION_HINT = "record_cancellation_hint"


@dataclass(frozen=True, slots=True)
class L2StateUpdateSuggestion:
    """建议 L2 未来记录的状态更新事实。"""

    suggestion_ref: TypedRef | None = None
    subject_state_ref: TypedRef | None = None
    suggestion_kind: StateUpdateSuggestionKind = StateUpdateSuggestionKind.UNKNOWN
    suggested_status: L2StateStatusKind = L2StateStatusKind.UNKNOWN
    missing_state_fields: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    reason_summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("L2StateUpdateSuggestion.advisory_only must remain true in L3 phase 2")
        if any(len(item) > 128 for item in self.missing_state_fields):
            raise ValueError("L2StateUpdateSuggestion.missing_state_fields entries must be short")
        if len(self.reason_summary) > 512:
            raise ValueError("L2StateUpdateSuggestion.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("L2StateUpdateSuggestion.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ProcessStateTransitionAdvice:
    """Run / Task / Turn / Step 流程状态转移建议。"""

    advice_ref: TypedRef | None = None
    subject_ref: TypedRef | None = None
    candidate: LifecycleTransitionCandidate | None = None
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    intent: LifecycleTransitionIntent = LifecycleTransitionIntent.UNKNOWN
    transition_score: float = 0.0
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_state_fields: tuple[str, ...] = field(default_factory=tuple)
    l2_state_update_suggestions: tuple[L2StateUpdateSuggestion, ...] = field(default_factory=tuple)
    future_l4_request_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_l5_boundary_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_l6_service_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    reason_summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.transition_score <= 1.0:
            raise ValueError("ProcessStateTransitionAdvice.transition_score must be between 0.0 and 1.0")
        if self.advisory_only is not True:
            raise ValueError("ProcessStateTransitionAdvice.advisory_only must remain true in L3 phase 2")
        if any(len(item) > 128 for item in self.missing_state_fields):
            raise ValueError("ProcessStateTransitionAdvice.missing_state_fields entries must be short")
        if len(self.reason_summary) > 512:
            raise ValueError("ProcessStateTransitionAdvice.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ProcessStateTransitionAdvice.schema_version cannot be empty")


def l2_status_hint_for_lifecycle(lifecycle: OrchestrationLifecycleKind) -> L2StateStatusKind:
    """把 L3 生命周期建议映射为 L2 状态码提示；不写入 L2。"""

    mapping = {
        OrchestrationLifecycleKind.CREATED: L2StateStatusKind.DECLARED,
        OrchestrationLifecycleKind.PREPARED: L2StateStatusKind.DECLARED,
        OrchestrationLifecycleKind.ACTIVE: L2StateStatusKind.ACTIVE,
        OrchestrationLifecycleKind.WAITING: L2StateStatusKind.WAITING,
        OrchestrationLifecycleKind.PAUSED: L2StateStatusKind.WAITING,
        OrchestrationLifecycleKind.BLOCKED: L2StateStatusKind.BLOCKED,
        OrchestrationLifecycleKind.FAILED: L2StateStatusKind.FAILED,
        OrchestrationLifecycleKind.CANCELLED: L2StateStatusKind.REVOKED,
        OrchestrationLifecycleKind.COMPLETED: L2StateStatusKind.COMPLETED,
        OrchestrationLifecycleKind.RESUMABLE: L2StateStatusKind.WAITING,
        OrchestrationLifecycleKind.ABANDONED: L2StateStatusKind.SUPERSEDED,
    }
    return mapping.get(lifecycle, L2StateStatusKind.UNKNOWN)


def build_process_state_transition_advice(
    candidate: LifecycleTransitionCandidate,
    l2_suggestion_ref: TypedRef | None = None,
) -> ProcessStateTransitionAdvice:
    """从生命周期候选生成流程状态转移建议。"""

    l2_suggestion = L2StateUpdateSuggestion(
        suggestion_ref=l2_suggestion_ref,
        subject_state_ref=candidate.subject_ref,
        suggestion_kind=StateUpdateSuggestionKind.RECORD_LIFECYCLE_HINT,
        suggested_status=l2_status_hint_for_lifecycle(candidate.candidate_lifecycle),
        missing_state_fields=candidate.missing_state_fields,
        evidence_refs=candidate.blocker_refs,
        reason_summary="record lifecycle hint only",
    )
    return ProcessStateTransitionAdvice(
        subject_ref=candidate.subject_ref,
        candidate=candidate,
        current_lifecycle=candidate.current_lifecycle,
        suggested_lifecycle=candidate.candidate_lifecycle,
        intent=candidate.intent,
        transition_score=candidate.score_hint,
        blocker_refs=candidate.blocker_refs,
        missing_state_fields=candidate.missing_state_fields,
        l2_state_update_suggestions=(l2_suggestion,),
        reason_summary="process transition advice only",
    )
