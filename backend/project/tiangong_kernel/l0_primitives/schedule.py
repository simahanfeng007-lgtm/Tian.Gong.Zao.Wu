"""L0 调度、触发、计时与唤醒引用事实语言原语。

本模块在 L0 中的职责：定义未来时间、周期、条件、计时、等待和唤醒相关的事实引用。
本模块只表达：调度、触发、计时、唤醒、重复规则和触发条件引用。
本模块明确不做：后台执行、周期解析、任务队列、线程、系统定时器或云调度绑定。
禁止事项：不得启动后台任务，不得创建计时器，不得自动唤醒对象。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef

class ScheduleKind(str, Enum):
    """调度类别：表达未来或周期性推进事实类型；UNKNOWN 表示类别未知。"""
    ONE_SHOT="one_shot"; RECURRING="recurring"; DELAYED="delayed"; DEADLINE="deadline"; MAINTENANCE="maintenance"; RECOVERY_CHECK="recovery_check"; MEMORY_DECAY="memory_decay"; BUDGET_RESET="budget_reset"; PLUGIN_TASK="plugin_task"; UNKNOWN="unknown"
class TriggerKind(str, Enum):
    """触发类别：表达后续行为触发来源；UNKNOWN 表示触发来源未知。"""
    TIME="time"; EVENT="event"; SIGNAL="signal"; METRIC_THRESHOLD="metric_threshold"; STATE_CHANGE="state_change"; HUMAN_APPROVAL="human_approval"; WEBHOOK="webhook"; RESOURCE_PRESSURE="resource_pressure"; FAILURE_DETECTED="failure_detected"; LIFECYCLE_CHANGE="lifecycle_change"; UNKNOWN="unknown"
class TimerKind(str, Enum):
    """计时类别：表达等待、超时、延迟、冷却等窗口；UNKNOWN 表示类别未知。"""
    DELAY="delay"; TIMEOUT="timeout"; COOLDOWN="cooldown"; LEASE_EXPIRY="lease_expiry"; APPROVAL_EXPIRY="approval_expiry"; RETRY_BACKOFF="retry_backoff"; SLEEP="sleep"; UNKNOWN="unknown"
class ScheduleState(str, Enum):
    """调度状态：表达调度或触发生命周期；UNKNOWN 表示状态未知。"""
    PROPOSED="proposed"; ACTIVE="active"; WAITING="waiting"; FIRED="fired"; MISFIRED="misfired"; PAUSED="paused"; CANCELLED="cancelled"; EXPIRED="expired"; ARCHIVED="archived"; UNKNOWN="unknown"
class TriggerState(str, Enum):
    """触发状态：表达触发事实生命周期；UNKNOWN 表示状态未知。"""
    PROPOSED="proposed"; ACTIVE="active"; WAITING="waiting"; FIRED="fired"; MISFIRED="misfired"; PAUSED="paused"; CANCELLED="cancelled"; EXPIRED="expired"; ARCHIVED="archived"; UNKNOWN="unknown"
class WakeupReason(str, Enum):
    """唤醒原因：表达等待对象恢复推进的原因；UNKNOWN 表示原因未知。"""
    TIME_ELAPSED="time_elapsed"; SIGNAL_RECEIVED="signal_received"; HUMAN_ACTION="human_action"; RESOURCE_AVAILABLE="resource_available"; FAILURE_HANDLED="failure_handled"; UNKNOWN="unknown"
@dataclass(frozen=True, slots=True)
class ScheduleRef:
    """调度引用。作用：表达 Run、Goal、Plan、Effect、Recovery、Memory、Forgetting、Policy 或 Plugin 在未来时间或周期内被启动、检查或推进的调度事实；所属 L0 边界：只保存 schedule_id、kind 与 state；不能执行调度。字段：value 为 schedule_id。"""
    value: RefId; kind: ScheduleKind=ScheduleKind.UNKNOWN; state: ScheduleState=ScheduleState.UNKNOWN; target_ref: TypedRef|None=None; window_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ScheduleRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class TriggerRef:
    """触发引用。作用：表达事件、条件、时间、信号、指标、外部输入或人工动作触发后续行为的事实；所属 L0 边界：只保存 trigger_id、kind 与 state；不能触发真实动作。字段：kind 为触发类别。"""
    value: RefId; kind: TriggerKind=TriggerKind.UNKNOWN; state: TriggerState=TriggerState.UNKNOWN; source_ref: TypedRef|None=None; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("TriggerRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class TimerRef:
    """计时引用。作用：表达计时、超时、延迟、冷却或等待窗口；所属 L0 边界：只保存 timer_id、kind 与 window_ref；不能启动真实计时。字段：kind 为计时类别。"""
    value: RefId; kind: TimerKind=TimerKind.UNKNOWN; window_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("TimerRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class WakeupRef:
    """唤醒引用。作用：表达休眠、暂停、等待中的对象被唤醒的事实；所属 L0 边界：只保存 wakeup_id、reason 与 target_ref；不能唤醒真实流程。字段：reason 为唤醒原因。"""
    value: RefId; reason: WakeupReason=WakeupReason.UNKNOWN; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("WakeupRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class RecurrenceRef:
    """重复规则引用。作用：表达重复发生的调度规则引用；所属 L0 边界：只保存 recurrence_id 与 schedule_ref；不能解析周期规则。字段：value 为重复规则引用 ID。"""
    value: RefId; schedule_ref: ScheduleRef|None=None; rule_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("RecurrenceRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class TriggerConditionRef:
    """触发条件引用。作用：表达触发条件引用；所属 L0 边界：只保存 condition_id 与 trigger_ref；不能判断条件。字段：value 为触发条件引用 ID。"""
    value: RefId; trigger_ref: TriggerRef|None=None; condition_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("TriggerConditionRef.schema_version cannot be empty")
