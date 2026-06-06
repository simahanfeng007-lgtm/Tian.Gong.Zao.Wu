"""L2 审计观察状态对象。

作用：记录与审计相关的观察事实引用及其运行、任务、工具、边界和安全关联。
边界：这是状态对象，不是观察器、采集器或监听器，不写审计日志、不签名、不验签、不归档。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class AuditObservationKind(str, Enum):
    """审计观察类型。

    作用：表达运行、任务、Skill、工具组、工具意图、动作、效果、边界、安全或资源审计观察标签。
    边界：这是状态标签，不写审计文件，不做签名验签，不生成候选对象。
    """

    RUN_AUDIT = "run_audit"
    TASK_AUDIT = "task_audit"
    SKILL_AUDIT = "skill_audit"
    TOOL_GROUP_AUDIT = "tool_group_audit"
    TOOL_INTENT_AUDIT = "tool_intent_audit"
    ACTION_AUDIT = "action_audit"
    EFFECT_AUDIT = "effect_audit"
    BOUNDARY_AUDIT = "boundary_audit"
    SECURITY_AUDIT = "security_audit"
    RESOURCE_AUDIT = "resource_audit"
    CANDIDATE_AUDIT_HINT = "candidate_audit_hint"
    UNKNOWN = "unknown"


class AuditObservationStatus(str, Enum):
    """审计观察状态。

    作用：表达审计观察已记录、已关联、已脱敏、不完整、冲突、过期或未知状态。
    边界：这是状态对象的状态标签，不写审计日志，不做最终责任归因。
    """

    NOTED = "noted"
    LINKED = "linked"
    REDACTED = "redacted"
    INCOMPLETE = "incomplete"
    CONFLICTED = "conflicted"
    STALE = "stale"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class AuditObservationState:
    """审计观察状态。

    作用：记录审计观察引用、帧、事件流、指标、运行、任务、Skill、工具、动作、效果、边界和安全引用。
    边界：这是状态对象，不是观察器、采集器或监听器，不写审计日志、不签名、不验签、不归档。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    audit_observation_ref: TypedRef | None = None
    audit_kind: AuditObservationKind = AuditObservationKind.UNKNOWN
    audit_status: AuditObservationStatus = AuditObservationStatus.UNKNOWN
    frame_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    event_stream_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metric_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    related_run_ref: TypedRef | None = None
    related_task_ref: TypedRef | None = None
    related_skill_ref: TypedRef | None = None
    related_tool_group_ref: TypedRef | None = None
    related_tool_intent_ref: TypedRef | None = None
    related_action_ref: TypedRef | None = None
    related_effect_ref: TypedRef | None = None
    related_boundary_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    related_security_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_summary: str | None = None
    audit_payload_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.audit_summary == "":
            raise ValueError("AuditObservationState.audit_summary cannot be empty when provided")
        if self.audit_summary is not None and len(self.audit_summary) > 512:
            raise ValueError("AuditObservationState.audit_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("AuditObservationState.schema_version cannot be empty")
