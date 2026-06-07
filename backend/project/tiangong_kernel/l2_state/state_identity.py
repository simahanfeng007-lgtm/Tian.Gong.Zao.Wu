"""L2 状态身份对象，只表达状态引用、类型和范围归属，不生成真实身份或查询状态。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.scope import ScopeRef


class L2StateKind(str, Enum):
    """L2 状态类型枚举；只描述状态事实所属类别，不代表后续阶段已经实现。"""

    UNKNOWN = "unknown"
    BASE = "base"
    AGENT = "agent"
    RUN = "run"
    TASK = "task"
    GOAL_PLAN = "goal_plan"
    SKILL = "skill"
    TOOL_GROUP = "tool_group"
    TOOL_INTENT = "tool_intent"
    MODEL = "model"
    BOUNDARY = "boundary"
    OBSERVATION = "observation"
    MEMORY_CONTEXT = "memory_context"
    CANDIDATE = "candidate"
    CHANGE = "change"
    VALIDATION = "validation"
    EXPERIMENT = "experiment"
    RECOVERY = "recovery"
    COMPONENT = "component"
    COMPATIBILITY = "compatibility"
    CATALOG = "catalog"
    CLOSURE = "closure"
    PROJECTION = "projection"
    MATH = "math"
    AFFECTIVE = "affective"
    DYNAMIC_DRIVE = "dynamic_drive"


@dataclass(frozen=True, slots=True)
class L2StateIdentity:
    """L2 状态身份。

    作用：记录一个 L2 状态对象的稳定引用、状态类型、父状态引用和范围引用。
    边界：不生成真实 ID，不注册状态，不查询状态，只表达身份事实。
    """

    state_ref: TypedRef
    kind: L2StateKind = L2StateKind.UNKNOWN
    parent_ref: TypedRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("L2StateIdentity.schema_version cannot be empty")
