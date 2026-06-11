"""L0 组件、模块、包、接口与边界引用事实语言原语。

本模块在 L0 中的职责：定义系统可组合、可替换、可治理单元的引用事实。
本模块只表达：组件、模块、包、摘要、版本、接口和边界引用。
本模块明确不做：组件加载、包安装、依赖解析、插件执行或热加载。
禁止事项：不得导入模块，不得安装包，不得加载插件，不得解析依赖。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class ComponentKind(str, Enum):
    """组件类别：只表达功能单元类型；UNKNOWN 表示类别未知。"""
    CORE_COMPONENT="core_component"; RUNTIME_COMPONENT="runtime_component"; POLICY_COMPONENT="policy_component"; MEMORY_COMPONENT="memory_component"; RECOVERY_COMPONENT="recovery_component"; SKILL_COMPONENT="skill_component"; TOOL_COMPONENT="tool_component"; ADAPTER_COMPONENT="adapter_component"; PLUGIN_COMPONENT="plugin_component"; UI_COMPONENT="ui_component"; UNKNOWN="unknown"
class ModuleKind(str, Enum):
    """模块类别：只表达模块化边界类型；UNKNOWN 表示类别未知。"""
    PYTHON_MODULE="python_module"; CONFIG_MODULE="config_module"; SCHEMA_MODULE="schema_module"; POLICY_MODULE="policy_module"; SKILL_MODULE="skill_module"; TOOL_MODULE="tool_module"; ADAPTER_MODULE="adapter_module"; PLUGIN_MODULE="plugin_module"; DOCUMENTATION_MODULE="documentation_module"; UNKNOWN="unknown"
class PackageKind(str, Enum):
    """包类别：只表达可分发集合类型；UNKNOWN 表示类别未知。"""
    CORE_PACKAGE="core_package"; PLUGIN_PACKAGE="plugin_package"; SKILL_PACKAGE="skill_package"; TOOL_PACKAGE="tool_package"; ADAPTER_PACKAGE="adapter_package"; POLICY_PACKAGE="policy_package"; SCHEMA_PACKAGE="schema_package"; ARTIFACT_PACKAGE="artifact_package"; DISTRIBUTION_PACKAGE="distribution_package"; UNKNOWN="unknown"
class ComponentState(str, Enum):
    """组件状态：只表达组件、模块或包生命周期；UNKNOWN 表示状态未知。"""
    DISCOVERED="discovered"; REGISTERED="registered"; AVAILABLE="available"; LOADED="loaded"; ACTIVE="active"; DEGRADED="degraded"; DISABLED="disabled"; QUARANTINED="quarantined"; DEPRECATED="deprecated"; REVOKED="revoked"; ARCHIVED="archived"; UNKNOWN="unknown"
class ModuleState(str, Enum):
    """模块状态：只表达模块生命周期；UNKNOWN 表示状态未知。"""
    DISCOVERED="discovered"; REGISTERED="registered"; AVAILABLE="available"; LOADED="loaded"; ACTIVE="active"; DEGRADED="degraded"; DISABLED="disabled"; QUARANTINED="quarantined"; DEPRECATED="deprecated"; REVOKED="revoked"; ARCHIVED="archived"; UNKNOWN="unknown"
class PackageState(str, Enum):
    """包状态：只表达包生命周期；UNKNOWN 表示状态未知。"""
    DISCOVERED="discovered"; REGISTERED="registered"; AVAILABLE="available"; LOADED="loaded"; ACTIVE="active"; DEGRADED="degraded"; DISABLED="disabled"; QUARANTINED="quarantined"; DEPRECATED="deprecated"; REVOKED="revoked"; ARCHIVED="archived"; UNKNOWN="unknown"
@dataclass(frozen=True, slots=True)
class PackageDigest:
    """包摘要。作用：表达包内容摘要引用；所属 L0 边界：只保存 digest 和 algorithm；不能验证签名或读取包内容。"""
    digest: str; algorithm: str="sha256"; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.digest: raise ValueError("PackageDigest.digest cannot be empty")
        if not self.schema_version: raise ValueError("PackageDigest.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class PackageVersionRef:
    """包版本引用。作用：表达包版本引用；所属 L0 边界：只保存 package_version_id 与 package_ref；不能安装或升级包。"""
    value: RefId; package_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("PackageVersionRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class ComponentInterfaceRef:
    """组件接口引用。作用：表达组件暴露的接口引用；所属 L0 边界：只保存 component_interface_id 与 component_ref；不能调用接口。"""
    value: RefId; component_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ComponentInterfaceRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class ComponentBoundaryRef:
    """组件边界引用。作用：表达组件的边界引用；所属 L0 边界：只保存 component_boundary_id 与 component_ref；不能执行隔离或加载。"""
    value: RefId; component_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ComponentBoundaryRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class ComponentRef:
    """组件引用。作用：表达系统中可组合、可替换、可治理的功能单元引用；所属 L0 边界：只保存 component_id、kind、state 和 boundary_ref；不能加载组件。"""
    value: RefId; kind: ComponentKind=ComponentKind.UNKNOWN; state: ComponentState=ComponentState.UNKNOWN; boundary_ref: ComponentBoundaryRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ComponentRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class ModuleRef:
    """模块引用。作用：表达代码、能力、策略、适配器或插件的模块化边界引用；所属 L0 边界：只保存 module_id、kind、state；不能导入模块。"""
    value: RefId; kind: ModuleKind=ModuleKind.UNKNOWN; state: ModuleState=ModuleState.UNKNOWN; component_ref: ComponentRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ModuleRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class PackageRef:
    """包引用。作用：表达可分发、可安装、可验证、可归档的一组组件或模块集合引用；所属 L0 边界：只保存 package_id、kind、state、digest、version_ref；不能安装或加载包。"""
    value: RefId; kind: PackageKind=PackageKind.UNKNOWN; state: PackageState=PackageState.UNKNOWN; digest: PackageDigest|None=None; version_ref: PackageVersionRef|None=None; module_refs: tuple[ModuleRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("PackageRef.schema_version cannot be empty")
