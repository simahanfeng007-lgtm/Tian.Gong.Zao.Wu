"""L0 资源、预算、限制与压力事实语言原语。

本模块在 L0 中的职责：定义外部世界和生命体运行相关资源的引用事实和值对象。
本模块只表达：资源引用、数量、使用、预算、限制、压力与能量预算。
本模块明确不做：真实资源分配、真实采集、额度扣减、上下文裁剪或网络配额执行。
禁止事项：不得管理真实资源，不得读取系统指标，不得执行限额策略。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class ResourceKind(str, Enum):
    """资源类别：只表达被占用、消耗、限制或恢复的资源类型；UNKNOWN 表示类别未知。

    COMPUTE：计算；MEMORY：内存；CONTEXT：上下文；STORAGE：存储；NETWORK：网络；EFFECT：副作用额度；
    ATTENTION：注意力；TIME：时间；ENERGY：能量；UNKNOWN：未知兜底。
    """
    COMPUTE="compute"; MEMORY="memory"; CONTEXT="context"; STORAGE="storage"; NETWORK="network"; EFFECT="effect"; ATTENTION="attention"; TIME="time"; ENERGY="energy"; UNKNOWN="unknown"

@dataclass(frozen=True, slots=True)
class ResourceQuantity:
    """资源数量。

    作用：表达资源数量和值对象。
    所属 L0 边界：只保存 amount、unit 与 kind，不采集真实资源。
    不能承担的上层职责：不能计量真实 CPU、内存、token 或网络配额。
    字段：amount 为数量；unit 为单位；kind 为资源类别。
    """
    amount: float = 0.0; unit: str = "unit"; kind: ResourceKind = ResourceKind.UNKNOWN; schema_version: str = "0.1"
    def __post_init__(self)->None:
        if not self.unit: raise ValueError("ResourceQuantity.unit cannot be empty")
        if not self.schema_version: raise ValueError("ResourceQuantity.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ResourceRef:
    """资源引用。

    作用：表达生命型智能体运行中被占用、被消耗、被限制或被恢复的对象引用。
    所属 L0 边界：只保存 resource_id、kind、owner_ref 与 scope_ref。
    不能承担的上层职责：不能分配、释放、采集或管理真实资源。
    字段：value 为资源引用 ID；owner_ref 为归属引用；scope_ref 为作用域引用。
    """
    value: RefId; kind: ResourceKind = ResourceKind.UNKNOWN; owner_ref: TypedRef|None = None; scope_ref: TypedRef|None = None; schema_version: str = "0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ResourceRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ResourceUsage:
    """资源使用事实。

    作用：表达某个资源被使用的事实引用和数量。
    所属 L0 边界：只保存 usage_id、resource_ref、quantity 与 actor_ref。
    不能承担的上层职责：不能扣减额度，不能阻断调用，不能采集系统指标。
    字段：value 为资源使用引用 ID；quantity 为使用数量。
    """
    value: RefId; resource_ref: ResourceRef|None = None; quantity: ResourceQuantity|None = None; actor_ref: TypedRef|None = None; schema_version: str = "0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ResourceUsage.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ResourceBudget:
    """资源预算引用。

    作用：表达资源预算边界的引用事实。
    所属 L0 边界：只保存 budget_id、resource_ref 与 quantity。
    不能承担的上层职责：不能优化预算，不能实际限制使用。
    字段：value 为预算引用 ID；resource_ref 为资源引用。
    """
    value: RefId; resource_ref: ResourceRef|None = None; quantity: ResourceQuantity|None = None; window_ref: TypedRef|None = None; schema_version: str = "0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ResourceBudget.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ResourceLimit:
    """资源限制引用。

    作用：表达资源可使用上限或边界引用。
    所属 L0 边界：只保存 limit_id、resource_ref、quantity 与 boundary_ref。
    不能承担的上层职责：不能执行限流、裁剪或拒绝策略。
    字段：value 为限制引用 ID；boundary_ref 为边界引用。
    """
    value: RefId; resource_ref: ResourceRef|None = None; quantity: ResourceQuantity|None = None; boundary_ref: TypedRef|None = None; schema_version: str = "0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ResourceLimit.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ResourcePressure:
    """资源压力事实。

    作用：表达资源接近限制、紧张或过载的事实。
    所属 L0 边界：只保存 pressure_id、resource_ref、usage_ref 与 pressure_value。
    不能承担的上层职责：不能触发降级或恢复算法。
    字段：pressure_value 为压力数值事实。
    """
    value: RefId; resource_ref: ResourceRef|None = None; usage_ref: ResourceUsage|None = None; pressure_value: float = 0.0; evidence_refs: tuple[TypedRef,...] = field(default_factory=tuple); schema_version: str = "0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ResourcePressure.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class EnergyBudget:
    """能量预算引用。

    作用：表达生命体运行能量预算的引用事实。
    所属 L0 边界：只保存 energy_budget_id、quantity 与 scope_ref。
    不能承担的上层职责：不能实现生物节律、调度或能耗管理。
    字段：value 为能量预算引用 ID；quantity 为能量数量事实。
    """
    value: RefId; quantity: ResourceQuantity|None = None; scope_ref: TypedRef|None = None; schema_version: str = "0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("EnergyBudget.schema_version cannot be empty")
