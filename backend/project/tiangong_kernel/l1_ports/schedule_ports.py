
"""L1 第八阶段调度、触发、定时与节律边界端口协议。

本模块在 L1 中的职责：定义调度意图、调度边界、触发意图、触发边界、定时引用、定时边界、节律提示和延后行动提示协议。
本模块定义哪些端口：ScheduleIntentPort、ScheduleBoundaryPort、TriggerIntentPort、TriggerBoundaryPort、TimerReferencePort、TimerBoundaryPort、CadenceHintPort、DeferredActionHintPort。
本模块不实现哪些能力：不启动调度器、不创建任务、不监听事件、不启动回调、不启动定时器、不延后执行动作。
本模块禁止事项：不得创建后台任务、不得访问消息队列、不得使用真实时间等待、不得连接外部系统。
本模块与 L2-L6 的关系：L2 可记录调度状态，L3 可编排调度意图，L4 可实现外部调度适配，L5 可隔离插件触发范围，L6 可提交子系统节律提示。
本模块如何服务工程生命体：为长期任务、周期节律和触发意图提供可审计的协议边界。
本模块如何维持大模型执行力与绝对边界：调度协议只表达自动化边界，不阻碍模型当前可执行行动链。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.event import EventRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.schedule import ScheduleRef, TimerRef, TriggerRef, RecurrenceRef
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.trace import TraceContext

from .envelope import PortBoundaryContext
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class ScheduleIntent:
    """调度意图对象。作用：表达某行动可能被调度的意图；边界：不启动调度器。"""
    schedule_ref: ScheduleRef
    target_ref: ResourceRef | None = None
    scope_ref: ScopeRef | None = None
    recurrence_ref: RecurrenceRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ScheduleBoundary:
    """调度边界对象。作用：表达哪些动作不能被自动调度；边界：不执行边界裁决。"""
    schedule_ref: ScheduleRef = None
    boundary: PortBoundary | None = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TriggerIntent:
    """触发意图对象。作用：表达事件、信号或观察可能触发后续处理；边界：不监听、不回调。"""
    trigger_ref: TriggerRef
    event_ref: EventRef | None = None
    signal_ref: SignalRef | None = None
    target_ref: ResourceRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TriggerBoundary:
    """触发边界对象。作用：表达触发可用范围；边界：不执行触发动作。"""
    trigger_ref: TriggerRef | None = None
    boundary: PortBoundary | None = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TimerReference:
    """定时器引用对象。作用：表达定时引用与目标；边界：不启动定时器。"""
    timer_ref: TimerRef
    target_ref: ResourceRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TimerBoundary:
    """定时边界对象。作用：表达定时边界；边界：不等待、不调度。"""
    timer_ref: TimerRef = None
    boundary: PortBoundary | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class CadenceHint:
    """节律提示对象。作用：表达周期、节律和频率提示；边界：不执行周期任务。"""
    hint_ref: ResourceRef
    schedule_ref: ScheduleRef = None
    timer_ref: TimerRef = None
    evidence_refs: tuple[ResourceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class DeferredActionHint:
    """延后行动提示对象。作用：表达某行动可延后处理；边界：不排队、不落盘、不后台运行。"""
    hint_ref: ResourceRef
    target_ref: ResourceRef | None = None
    schedule_ref: ScheduleRef = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ScheduleIntentRequest:
    """调度意图请求。作用：提交调度意图；边界：不创建任务。"""
    intent: ScheduleIntent
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ScheduleIntentResponse:
    """调度意图响应。作用：返回调度意图；边界：不启动调度器。"""
    intent: ScheduleIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ScheduleBoundaryRequest:
    """调度边界请求。作用：声明调度边界；边界：不裁决。"""
    boundary: ScheduleBoundary
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ScheduleBoundaryResponse:
    """调度边界响应。作用：返回调度边界；边界：不阻断当前行动。"""
    boundary: ScheduleBoundary
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TriggerIntentRequest:
    """触发意图请求。作用：提交触发意图；边界：不监听事件。"""
    intent: TriggerIntent
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TriggerIntentResponse:
    """触发意图响应。作用：返回触发意图；边界：不启动回调。"""
    intent: TriggerIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TriggerBoundaryRequest:
    """触发边界请求。作用：声明触发边界；边界：不执行触发动作。"""
    boundary: TriggerBoundary
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TriggerBoundaryResponse:
    """触发边界响应。作用：返回触发边界；边界：不改变状态。"""
    boundary: TriggerBoundary
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TimerReferenceRequest:
    """定时器引用请求。作用：声明定时引用；边界：不启动 timer。"""
    reference: TimerReference
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TimerReferenceResponse:
    """定时器引用响应。作用：返回定时引用；边界：不等待。"""
    reference: TimerReference
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TimerBoundaryRequest:
    """定时边界请求。作用：声明定时边界；边界：不使用真实时间调度。"""
    boundary: TimerBoundary
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TimerBoundaryResponse:
    """定时边界响应。作用：返回定时边界；边界：不创建定时任务。"""
    boundary: TimerBoundary
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class CadenceHintRequest:
    """节律提示请求。作用：提交节律提示；边界：不执行周期任务。"""
    hint: CadenceHint
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class CadenceHintResponse:
    """节律提示响应。作用：返回节律提示；边界：不调度。"""
    hint: CadenceHint
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class DeferredActionHintRequest:
    """延后行动提示请求。作用：提交延后提示；边界：不排队。"""
    hint: DeferredActionHint
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class DeferredActionHintResponse:
    """延后行动提示响应。作用：返回延后提示；边界：不后台运行。"""
    hint: DeferredActionHint
    schema_version: str = "0.1"


class ScheduleIntentPort(ABC):
    """调度意图端口。中文名称：调度意图端口。端口职责：定义调度意图协议。输入输出边界：输入 ScheduleIntentRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段调度边界。不承担的实现职责：不启动调度器、不创建任务。如何服务大模型执行力：让模型表达未来行动意图。如何维持绝对边界：意图不等于自动执行。与后续 L2-L6 的关系：供状态和编排层引用。"""
    @abstractmethod
    def submit_schedule_intent(self, request: ScheduleIntentRequest, trace: TraceContext) -> PortResult[ScheduleIntentResponse]:
        """声明调度意图协议。"""
        raise NotImplementedError


class ScheduleBoundaryPort(ABC):
    """调度边界端口。中文名称：调度边界端口。端口职责：定义调度边界协议。输入输出边界：输入 ScheduleBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段调度边界。不承担的实现职责：不阻断当前行动。如何服务大模型执行力：只限制自动化越界。如何维持绝对边界：边界说明不触发执行。与后续 L2-L6 的关系：供调度适配与插件隔离引用。"""
    @abstractmethod
    def describe_schedule_boundary(self, request: ScheduleBoundaryRequest, trace: TraceContext) -> PortResult[ScheduleBoundaryResponse]:
        """声明调度边界协议。"""
        raise NotImplementedError


class TriggerIntentPort(ABC):
    """触发意图端口。中文名称：触发意图端口。端口职责：定义触发意图协议。输入输出边界：输入 TriggerIntentRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段触发边界。不承担的实现职责：不监听、不回调。如何服务大模型执行力：让观察可形成候选触发。如何维持绝对边界：触发意图不能绕过边界。与后续 L2-L6 的关系：供运行编排与插件子系统引用。"""
    @abstractmethod
    def submit_trigger_intent(self, request: TriggerIntentRequest, trace: TraceContext) -> PortResult[TriggerIntentResponse]:
        """声明触发意图协议。"""
        raise NotImplementedError


class TriggerBoundaryPort(ABC):
    """触发边界端口。中文名称：触发边界端口。端口职责：定义触发边界协议。输入输出边界：输入 TriggerBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段触发边界。不承担的实现职责：不执行触发动作。如何服务大模型执行力：让自动触发保持可解释。如何维持绝对边界：边界不产生回调。与后续 L2-L6 的关系：供事件和插件边界引用。"""
    @abstractmethod
    def describe_trigger_boundary(self, request: TriggerBoundaryRequest, trace: TraceContext) -> PortResult[TriggerBoundaryResponse]:
        """声明触发边界协议。"""
        raise NotImplementedError


class TimerReferencePort(ABC):
    """定时器引用端口。中文名称：定时器引用端口。端口职责：定义定时器引用协议。输入输出边界：输入 TimerReferenceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段定时边界。不承担的实现职责：不启动定时器、不等待。如何服务大模型执行力：让延时需求有引用边界。如何维持绝对边界：定时引用不是后台任务。与后续 L2-L6 的关系：供调度和状态层引用。"""
    @abstractmethod
    def reference_timer(self, request: TimerReferenceRequest, trace: TraceContext) -> PortResult[TimerReferenceResponse]:
        """声明定时器引用协议。"""
        raise NotImplementedError


class TimerBoundaryPort(ABC):
    """定时边界端口。中文名称：定时边界端口。端口职责：定义定时边界协议。输入输出边界：输入 TimerBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段定时边界。不承担的实现职责：不做真实时间调度。如何服务大模型执行力：避免时间边界打断执行链。如何维持绝对边界：不得由边界协议创建任务。与后续 L2-L6 的关系：供调度适配引用。"""
    @abstractmethod
    def describe_timer_boundary(self, request: TimerBoundaryRequest, trace: TraceContext) -> PortResult[TimerBoundaryResponse]:
        """声明定时边界协议。"""
        raise NotImplementedError


class CadenceHintPort(ABC):
    """节律提示端口。中文名称：节律提示端口。端口职责：定义节律提示协议。输入输出边界：输入 CadenceHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段节律协议。不承担的实现职责：不执行周期任务。如何服务大模型执行力：给长期工程生命体提供节律参考。如何维持绝对边界：提示不触发自动化。与后续 L2-L6 的关系：供生命体状态和学习链引用。"""
    @abstractmethod
    def submit_cadence_hint(self, request: CadenceHintRequest, trace: TraceContext) -> PortResult[CadenceHintResponse]:
        """声明节律提示协议。"""
        raise NotImplementedError


class DeferredActionHintPort(ABC):
    """延后行动提示端口。中文名称：延后行动提示端口。端口职责：定义延后行动提示协议。输入输出边界：输入 DeferredActionHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段调度协议。不承担的实现职责：不排队、不后台运行。如何服务大模型执行力：让不能即时执行的动作保留可解释提示。如何维持绝对边界：延后提示不是任务创建。与后续 L2-L6 的关系：供编排层和状态层引用。"""
    @abstractmethod
    def submit_deferred_action_hint(self, request: DeferredActionHintRequest, trace: TraceContext) -> PortResult[DeferredActionHintResponse]:
        """声明延后行动提示协议。"""
        raise NotImplementedError
