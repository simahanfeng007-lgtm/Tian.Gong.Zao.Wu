"""L2 目标计划关系状态对象，只串联目标与计划引用，不生成计划或调度任务。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.goal import GoalRef
from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.plan import PlanRef
from tiangong_kernel.l0_primitives.scope import ScopeRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class GoalPlanRelationKind(str, Enum):
    """目标计划关系枚举。

    作用：表达目标与计划之间的声明性关系。
    边界：不优化目标，不生成计划，不执行计划或调度任务。
    """

    UNKNOWN = "unknown"
    GOAL_ONLY = "goal_only"
    PLAN_ONLY = "plan_only"
    PLAN_FOR_GOAL = "plan_for_goal"
    GOAL_BLOCKED_BY_PLAN = "goal_blocked_by_plan"
    PLAN_BLOCKED_BY_GOAL = "plan_blocked_by_goal"
    GOAL_PLAN_MISMATCH = "goal_plan_mismatch"
    RECOVERY_PLAN_FOR_GOAL = "recovery_plan_for_goal"


@dataclass(frozen=True, slots=True)
class GoalPlanState:
    """目标计划关系状态。

    作用：记录 GoalRef、PlanRef 与当前运行/任务/范围之间的状态关系。
    边界：不生成计划，不排序步骤，不调度任务，不执行计划，只记录关系事实。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    goal_ref: GoalRef | None = None
    plan_ref: PlanRef | None = None
    relation: GoalPlanRelationKind = GoalPlanRelationKind.UNKNOWN
    scope_ref: ScopeRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    plan_origin_ref: TypedRef | None = None
    success_criteria_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    failure_criteria_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    blocking_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    boundary: L2StateBoundary | None = None
    budget_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    quota_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    rate_limit_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    resource_pressure_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("GoalPlanState.schema_version cannot be empty")
