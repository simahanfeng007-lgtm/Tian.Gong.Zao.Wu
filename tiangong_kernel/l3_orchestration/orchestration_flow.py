"""L3 主运行编排 Flow 被动规格。

本模块只描述主运行编排链路中的请求、建议、投影和交接引用。它不是运行循环，
不读取文件、不访问网络、不调用模型或工具、不写状态、不做权限裁决。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


_LOWER_SNAKE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class OrchestrationFlowKind(str, Enum):
    """L3 Flow 类型枚举，只用于标识被动规格节点。"""

    RUN = "run"
    STEP = "step"
    CONTEXT_PREPARATION = "context_preparation"
    MODEL_INTENT = "model_intent"
    SKILL_TOOL_RELEASE = "skill_tool_release"
    ACTION_INTENT = "action_intent"
    EFFECT_REQUEST = "effect_request"
    DECISION = "decision"
    LEASE_VALIDATION = "lease_validation"
    EXECUTION_HANDOFF = "execution_handoff"
    OBSERVATION_FEEDBACK = "observation_feedback"
    EVENT_APPEND = "event_append"
    STATE_TRANSITION = "state_transition"
    AUDIT = "audit"
    RECOVERY = "recovery"
    HUMAN_APPROVAL = "human_approval"
    SCHEDULE_TRIGGER_TIMER = "schedule_trigger_timer"


def _ensure_short_text(value: str, field_name: str, limit: int = 128) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _ensure_reason_codes(reason_codes: tuple[str, ...], field_name: str) -> None:
    for reason_code in reason_codes:
        _ensure_short_text(reason_code, field_name, 128)
        if not _LOWER_SNAKE_RE.match(reason_code):
            raise ValueError(f"{field_name} must use lower_snake_case")


@dataclass(frozen=True, slots=True)
class OrchestrationFlowNodeRef:
    """Flow 节点引用，不代表可执行节点。"""

    node_ref: TypedRef | None = None
    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.RUN
    source_flow_ref: TypedRef | None = None
    label: str = ""
    node_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.label, "OrchestrationFlowNodeRef.label", 128)
        _ensure_true(self.node_only, "OrchestrationFlowNodeRef.node_only")
        if not self.schema_version:
            raise ValueError("OrchestrationFlowNodeRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationFlowEdge:
    """Flow 边引用，只描述建议顺序。"""

    edge_ref: TypedRef | None = None
    from_node_ref: TypedRef | None = None
    to_node_ref: TypedRef | None = None
    edge_kind: str = "next_hint"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    edge_only: bool = True
    no_execution: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.edge_kind, "OrchestrationFlowEdge.edge_kind", 128)
        _ensure_reason_codes(self.reason_codes, "OrchestrationFlowEdge.reason_codes")
        _ensure_true(self.edge_only, "OrchestrationFlowEdge.edge_only")
        _ensure_true(self.no_execution, "OrchestrationFlowEdge.no_execution")
        if not self.schema_version:
            raise ValueError("OrchestrationFlowEdge.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationFlowInvariant:
    """Flow 边界不变量声明。"""

    invariant_ref: TypedRef | None = None
    invariant_name: str = "flow_is_passive_spec"
    blocked_terms: tuple[str, ...] = (
        "model_call",
        "tool_call",
        "state_write",
        "permission_result",
        "ticket_issue",
        "lease_grant",
    )
    invariant_only: bool = True
    no_execution: bool = True
    no_decision: bool = True
    no_persistence: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.invariant_name, "OrchestrationFlowInvariant.invariant_name", 128)
        for item in self.blocked_terms:
            _ensure_short_text(item, "OrchestrationFlowInvariant.blocked_terms", 128)
        _ensure_true(self.invariant_only, "OrchestrationFlowInvariant.invariant_only")
        _ensure_true(self.no_execution, "OrchestrationFlowInvariant.no_execution")
        _ensure_true(self.no_decision, "OrchestrationFlowInvariant.no_decision")
        _ensure_true(self.no_persistence, "OrchestrationFlowInvariant.no_persistence")
        if not self.schema_version:
            raise ValueError("OrchestrationFlowInvariant.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationFlowSpec:
    """Flow 规格基础对象，只保存引用、建议和边界字段。"""

    flow_ref: TypedRef | None = None
    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.RUN
    source_run_ref: TypedRef | None = None
    source_task_ref: TypedRef | None = None
    source_turn_ref: TypedRef | None = None
    source_step_ref: TypedRef | None = None
    input_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    output_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    output_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    output_projection_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    prerequisite_flow_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    next_flow_hints: tuple[str, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    request_only: bool = True
    advisory_only: bool = True
    reference_only: bool = True
    no_execution: bool = True
    no_decision: bool = True
    no_persistence: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.flow_kind, OrchestrationFlowKind):
            raise ValueError("OrchestrationFlowSpec.flow_kind must use OrchestrationFlowKind")
        for item in self.next_flow_hints:
            _ensure_short_text(item, "OrchestrationFlowSpec.next_flow_hints", 128)
        _ensure_reason_codes(self.reason_codes, "OrchestrationFlowSpec.reason_codes")
        _ensure_true(self.request_only, "OrchestrationFlowSpec.request_only")
        _ensure_true(self.advisory_only, "OrchestrationFlowSpec.advisory_only")
        _ensure_true(self.reference_only, "OrchestrationFlowSpec.reference_only")
        _ensure_true(self.no_execution, "OrchestrationFlowSpec.no_execution")
        _ensure_true(self.no_decision, "OrchestrationFlowSpec.no_decision")
        _ensure_true(self.no_persistence, "OrchestrationFlowSpec.no_persistence")
        if not self.schema_version:
            raise ValueError("OrchestrationFlowSpec.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RunOrchestrationFlow(OrchestrationFlowSpec):
    """Run 级主链规格。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.RUN
    next_flow_hints: tuple[str, ...] = ("context_preparation",)


@dataclass(frozen=True, slots=True)
class StepOrchestrationFlow(OrchestrationFlowSpec):
    """Step 级主链规格。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.STEP
    next_flow_hints: tuple[str, ...] = ("context_preparation",)


@dataclass(frozen=True, slots=True)
class ContextPreparationFlow(OrchestrationFlowSpec):
    """上下文准备 Flow，只输出上下文引用。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.CONTEXT_PREPARATION
    next_flow_hints: tuple[str, ...] = ("model_intent",)


@dataclass(frozen=True, slots=True)
class ModelIntentFlow(OrchestrationFlowSpec):
    """模型意图 Flow，只输出意图建议引用。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.MODEL_INTENT
    next_flow_hints: tuple[str, ...] = ("skill_tool_release", "action_intent")


@dataclass(frozen=True, slots=True)
class SkillToolReleaseFlow(OrchestrationFlowSpec):
    """Skill 直显与工具释放 Flow，只表达候选、租约和边界引用。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.SKILL_TOOL_RELEASE
    skill_display_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    tool_group_release_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    lease_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_review_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    next_flow_hints: tuple[str, ...] = ("action_intent",)


@dataclass(frozen=True, slots=True)
class ActionIntentFlow(OrchestrationFlowSpec):
    """动作意图 Flow，只输出动作意图引用。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.ACTION_INTENT
    next_flow_hints: tuple[str, ...] = ("effect_request",)


@dataclass(frozen=True, slots=True)
class EffectRequestFlow(OrchestrationFlowSpec):
    """效果请求 Flow，只表达 effect、side_effect、audit 与 boundary 引用。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.EFFECT_REQUEST
    effect_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    side_effect_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    next_flow_hints: tuple[str, ...] = ("decision",)


@dataclass(frozen=True, slots=True)
class DecisionFlow(OrchestrationFlowSpec):
    """边界请求 Flow，只输出未来决策请求引用，不产出裁决。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.DECISION
    boundary_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    risk_review_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    policy_review_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    next_flow_hints: tuple[str, ...] = ("lease_validation", "human_approval")


@dataclass(frozen=True, slots=True)
class LeaseValidationFlow(OrchestrationFlowSpec):
    """租约校验 Flow，只表达租约检查引用，不授予或续租。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.LEASE_VALIDATION
    lease_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    lease_validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    lease_granted: bool = False
    next_flow_hints: tuple[str, ...] = ("execution_handoff",)

    def __post_init__(self) -> None:
        OrchestrationFlowSpec.__post_init__(self)
        if self.lease_granted:
            raise ValueError("LeaseValidationFlow cannot grant leases")


@dataclass(frozen=True, slots=True)
class ExecutionHandoffFlow(OrchestrationFlowSpec):
    """执行交接 Flow，只表达 L4/L5/L6 handoff 引用，不调度执行。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.EXECUTION_HANDOFF
    l4_handoff_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l5_handoff_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l6_handoff_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    execution_precondition_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    next_flow_hints: tuple[str, ...] = ("observation_feedback",)


@dataclass(frozen=True, slots=True)
class ObservationFeedbackFlow(OrchestrationFlowSpec):
    """观察反馈 Flow，只表达观察、结果回流和审计引用。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.OBSERVATION_FEEDBACK
    observation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    result_return_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    failure_return_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    next_flow_hints: tuple[str, ...] = ("event_append", "audit")


@dataclass(frozen=True, slots=True)
class EventAppendFlow(OrchestrationFlowSpec):
    """事件追加 Flow，只表达事件追加请求引用，不写事件存储。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.EVENT_APPEND
    event_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    event_store_write: bool = False
    next_flow_hints: tuple[str, ...] = ("state_transition",)

    def __post_init__(self) -> None:
        OrchestrationFlowSpec.__post_init__(self)
        if self.event_store_write:
            raise ValueError("EventAppendFlow cannot write event storage")


@dataclass(frozen=True, slots=True)
class StateTransitionFlow(OrchestrationFlowSpec):
    """状态迁移 Flow，只表达 L2 状态更新建议引用。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.STATE_TRANSITION
    l2_state_update_suggestion_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    state_write: bool = False
    next_flow_hints: tuple[str, ...] = ("audit",)

    def __post_init__(self) -> None:
        OrchestrationFlowSpec.__post_init__(self)
        if self.state_write:
            raise ValueError("StateTransitionFlow cannot write L2 state")


@dataclass(frozen=True, slots=True)
class RecoveryFlow(OrchestrationFlowSpec):
    """恢复 Flow，只表达恢复、重规划和降级引用。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.RECOVERY
    recovery_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    replan_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    fallback_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    next_flow_hints: tuple[str, ...] = ("context_preparation", "audit")


@dataclass(frozen=True, slots=True)
class AuditFlow(OrchestrationFlowSpec):
    """审计 Flow，只表达审计需求与证据引用，不写审计存储。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.AUDIT
    audit_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_store_write: bool = False
    next_flow_hints: tuple[str, ...] = ("event_append", "recovery")

    def __post_init__(self) -> None:
        OrchestrationFlowSpec.__post_init__(self)
        if self.audit_store_write:
            raise ValueError("AuditFlow cannot write audit storage")


@dataclass(frozen=True, slots=True)
class ScheduleTriggerTimerFlow(OrchestrationFlowSpec):
    """定时触发 Flow，只表达延迟、重试、过期和恢复引用。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.SCHEDULE_TRIGGER_TIMER
    schedule_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trigger_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    timer_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    background_task_started: bool = False
    next_flow_hints: tuple[str, ...] = ("context_preparation", "recovery")

    def __post_init__(self) -> None:
        OrchestrationFlowSpec.__post_init__(self)
        if self.background_task_started:
            raise ValueError("ScheduleTriggerTimerFlow cannot start background tasks")


@dataclass(frozen=True, slots=True)
class HumanApprovalFlow(OrchestrationFlowSpec):
    """人工确认 Flow，只表达等待、恢复、过期和拒绝引用。"""

    flow_kind: OrchestrationFlowKind = OrchestrationFlowKind.HUMAN_APPROVAL
    approval_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    wait_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    resume_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    expiration_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    denial_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confirmation_ticket_issued: bool = False
    next_flow_hints: tuple[str, ...] = ("lease_validation", "recovery")

    def __post_init__(self) -> None:
        OrchestrationFlowSpec.__post_init__(self)
        if self.confirmation_ticket_issued:
            raise ValueError("HumanApprovalFlow cannot issue confirmation tickets")


@dataclass(frozen=True, slots=True)
class CanonicalRunLoopFlowBundle:
    """标准主运行 Flow 束，只记录规范顺序。"""

    bundle_ref: TypedRef | None = None
    flow_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    ordered_flow_kinds: tuple[OrchestrationFlowKind, ...] = (
        OrchestrationFlowKind.CONTEXT_PREPARATION,
        OrchestrationFlowKind.MODEL_INTENT,
        OrchestrationFlowKind.SKILL_TOOL_RELEASE,
        OrchestrationFlowKind.ACTION_INTENT,
        OrchestrationFlowKind.EFFECT_REQUEST,
        OrchestrationFlowKind.DECISION,
        OrchestrationFlowKind.LEASE_VALIDATION,
        OrchestrationFlowKind.EXECUTION_HANDOFF,
        OrchestrationFlowKind.OBSERVATION_FEEDBACK,
        OrchestrationFlowKind.EVENT_APPEND,
        OrchestrationFlowKind.STATE_TRANSITION,
        OrchestrationFlowKind.AUDIT,
        OrchestrationFlowKind.RECOVERY,
        OrchestrationFlowKind.HUMAN_APPROVAL,
        OrchestrationFlowKind.SCHEDULE_TRIGGER_TIMER,
    )
    invariants: tuple[OrchestrationFlowInvariant, ...] = field(default_factory=lambda: (OrchestrationFlowInvariant(),))
    bundle_only: bool = True
    request_only: bool = True
    advisory_only: bool = True
    reference_only: bool = True
    no_execution: bool = True
    no_decision: bool = True
    no_persistence: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.bundle_only, "CanonicalRunLoopFlowBundle.bundle_only")
        _ensure_true(self.request_only, "CanonicalRunLoopFlowBundle.request_only")
        _ensure_true(self.advisory_only, "CanonicalRunLoopFlowBundle.advisory_only")
        _ensure_true(self.reference_only, "CanonicalRunLoopFlowBundle.reference_only")
        _ensure_true(self.no_execution, "CanonicalRunLoopFlowBundle.no_execution")
        _ensure_true(self.no_decision, "CanonicalRunLoopFlowBundle.no_decision")
        _ensure_true(self.no_persistence, "CanonicalRunLoopFlowBundle.no_persistence")
        if OrchestrationFlowKind.EFFECT_REQUEST not in self.ordered_flow_kinds:
            raise ValueError("CanonicalRunLoopFlowBundle must include effect_request")
        if OrchestrationFlowKind.HUMAN_APPROVAL not in self.ordered_flow_kinds:
            raise ValueError("CanonicalRunLoopFlowBundle must include human_approval")
        if OrchestrationFlowKind.SCHEDULE_TRIGGER_TIMER not in self.ordered_flow_kinds:
            raise ValueError("CanonicalRunLoopFlowBundle must include schedule_trigger_timer")
        if not self.schema_version:
            raise ValueError("CanonicalRunLoopFlowBundle.schema_version cannot be empty")


MainRunLoopFlowSpec = CanonicalRunLoopFlowBundle
