"""L0 价值、偏好、目标取向与权衡事实语言原语。

本模块在 L0 中的职责：定义价值取向、偏好、目标取向、效用信号和权衡引用事实。
本模块只表达：系统、用户、组织、政策或运行模式所引用的价值、偏好和目标事实。
本模块明确不做：价值观模型、偏好学习、奖励模型、伦理推理、效用优化或多目标优化。
禁止事项：不得训练偏好，不得计算道德判断，不得自动优化目标。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class ValueKind(str, Enum):
    """价值类别：只表达价值取向类型；UNKNOWN 表示类别未知。

    SAFETY：安全；HELPFULNESS：有用性；TRUTHFULNESS：真实性；PRIVACY：隐私；AUTONOMY：自治；
    STABILITY：稳定；EXECUTION_POWER：执行力；RESOURCE_EFFICIENCY：资源效率；CONTINUITY：连续性；
    USER_CONTROL：用户控制；TRANSPARENCY：透明；UNKNOWN：未知兜底。
    """
    SAFETY="safety"; HELPFULNESS="helpfulness"; TRUTHFULNESS="truthfulness"; PRIVACY="privacy"; AUTONOMY="autonomy"; STABILITY="stability"; EXECUTION_POWER="execution_power"; RESOURCE_EFFICIENCY="resource_efficiency"; CONTINUITY="continuity"; USER_CONTROL="user_control"; TRANSPARENCY="transparency"; UNKNOWN="unknown"

class PreferenceKind(str, Enum):
    """偏好类别：只表达偏好来源类型；UNKNOWN 表示类别未知。

    USER_PREFERENCE：用户偏好；SYSTEM_PREFERENCE：系统偏好；ORGANIZATION_PREFERENCE：组织偏好；MODE_PREFERENCE：模式偏好；
    CONTEXTUAL_PREFERENCE：上下文偏好；LEARNED_PREFERENCE：学习得到的偏好引用；UNKNOWN：未知兜底。
    """
    USER_PREFERENCE="user_preference"; SYSTEM_PREFERENCE="system_preference"; ORGANIZATION_PREFERENCE="organization_preference"; MODE_PREFERENCE="mode_preference"; CONTEXTUAL_PREFERENCE="contextual_preference"; LEARNED_PREFERENCE="learned_preference"; UNKNOWN="unknown"

class ObjectiveKind(str, Enum):
    """目标取向类别：只表达可被满足或权衡的目标类型；UNKNOWN 表示类别未知。

    TASK_SUCCESS：任务成功；RISK_MINIMIZATION：风险最小化；RESOURCE_OPTIMIZATION：资源优化；RECOVERY：恢复；
    LEARNING：学习；MEMORY_RETENTION：记忆保留；FORGETTING_CLEANUP：遗忘清理；COMPLIANCE：合规；USER_SATISFACTION：用户满意；UNKNOWN：未知兜底。
    """
    TASK_SUCCESS="task_success"; RISK_MINIMIZATION="risk_minimization"; RESOURCE_OPTIMIZATION="resource_optimization"; RECOVERY="recovery"; LEARNING="learning"; MEMORY_RETENTION="memory_retention"; FORGETTING_CLEANUP="forgetting_cleanup"; COMPLIANCE="compliance"; USER_SATISFACTION="user_satisfaction"; UNKNOWN="unknown"

class PreferenceState(str, Enum):
    """偏好状态：只表达偏好生命周期；UNKNOWN 表示状态未知。

    PROPOSED：提议；ACTIVE：活动；OVERRIDDEN：被覆盖；CONFLICTED：冲突；DEPRECATED：弃用；REVOKED：撤销；ARCHIVED：归档；UNKNOWN：未知兜底。
    """
    PROPOSED="proposed"; ACTIVE="active"; OVERRIDDEN="overridden"; CONFLICTED="conflicted"; DEPRECATED="deprecated"; REVOKED="revoked"; ARCHIVED="archived"; UNKNOWN="unknown"

@dataclass(frozen=True, slots=True)
class ObjectivePriority:
    """目标取向优先级。

    作用：表达目标取向的优先级数值事实。
    所属 L0 边界：只保存 objective_priority 数值，不做优化或排序。
    不能承担的上层职责：不能执行多目标优化，不能裁决价值冲突。
    字段：priority 为优先级数值。
    """
    priority: int=0; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ObjectivePriority.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ValueRef:
    """价值引用。

    作用：表达系统、用户、组织、政策或运行模式所引用的价值取向。
    所属 L0 边界：只保存 value_id、kind 与 source_ref。
    不能承担的上层职责：不能进行伦理推理，不能输出道德判断。
    字段：value 为价值引用 ID；kind 为价值类别；source_ref 为来源引用。
    """
    value: RefId; kind: ValueKind=ValueKind.UNKNOWN; source_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ValueRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class PreferenceRef:
    """偏好引用。

    作用：表达多个可行选择之间的偏好事实。
    所属 L0 边界：只保存 preference_id、kind、state、value_ref 与 evidence_refs。
    不能承担的上层职责：不能学习偏好，不能更新用户画像，不能执行选择算法。
    字段：value 为偏好引用 ID；kind 为偏好类别；state 为偏好状态。
    """
    value: RefId; kind: PreferenceKind=PreferenceKind.UNKNOWN; state: PreferenceState=PreferenceState.UNKNOWN; value_ref: ValueRef|None=None; evidence_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("PreferenceRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ObjectiveRef:
    """目标取向引用。

    作用：表达可被满足、约束或权衡的目标取向。
    所属 L0 边界：只保存 objective_id、kind 与 objective_priority。
    不能承担的上层职责：不能做目标优化，不能调度任务，不能决定行动。
    字段：value 为目标取向引用 ID；kind 为目标取向类别；objective_priority 为目标取向优先级。
    """
    value: RefId; kind: ObjectiveKind=ObjectiveKind.UNKNOWN; objective_priority: ObjectivePriority|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ObjectiveRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class UtilitySignalRef:
    """效用信号引用。

    作用：表达某个行动、计划、结果或状态对目标或价值的效用信号引用。
    所属 L0 边界：只保存 utility_signal_id、target_ref、objective_ref 与 value_ref。
    不能承担的上层职责：不能计算效用，不能训练奖励模型，不能优化决策。
    字段：value 为效用信号引用 ID；target_ref 为目标对象引用。
    """
    value: RefId; target_ref: TypedRef|None=None; objective_ref: ObjectiveRef|None=None; value_ref: ValueRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("UtilitySignalRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class TradeoffRef:
    """权衡引用。

    作用：表达多个价值、偏好、目标之间存在权衡关系的引用事实。
    所属 L0 边界：只保存 tradeoff_id、value_refs、preference_refs 与 objective_refs。
    不能承担的上层职责：不能做权衡算法，不能给出最终价值判断。
    字段：value 为权衡引用 ID；value_refs 为价值引用集合；objective_refs 为目标取向引用集合。
    """
    value: RefId; value_refs: tuple[ValueRef,...]=field(default_factory=tuple); preference_refs: tuple[PreferenceRef,...]=field(default_factory=tuple); objective_refs: tuple[ObjectiveRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("TradeoffRef.schema_version cannot be empty")
