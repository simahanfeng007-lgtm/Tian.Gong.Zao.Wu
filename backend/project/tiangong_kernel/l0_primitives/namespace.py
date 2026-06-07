"""L0 命名空间、名称、登记边界与别名事实语言原语。

本模块在 L0 中的职责：定义名称所属域、稳定名称、全限定名、登记边界、名称绑定、别名与弃用引用。
本模块只表达：命名相关引用事实和状态事实。
本模块明确不做：名字解析、服务发现、动态导入、冲突自动处理或目录实现。
禁止事项：不得访问外部目录，不得加载模块，不得处理真实服务地址。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef

class NamespaceKind(str, Enum):
    """命名空间类别：表达名字所属的命名域；UNKNOWN 表示命名域未知。"""
    CORE="core"; EVENT="event"; METRIC="metric"; SIGNAL="signal"; POLICY="policy"; CONTRACT="contract"; SKILL="skill"; TOOL="tool"; ADAPTER="adapter"; PLUGIN="plugin"; ARTIFACT="artifact"; RESOURCE="resource"; EXTERNAL="external"; UNKNOWN="unknown"
class RegistryKind(str, Enum):
    """登记域类别：表达负责登记或治理某类名称的边界；UNKNOWN 表示登记域未知。"""
    TYPE_REGISTRY="type_registry"; EVENT_REGISTRY="event_registry"; SCHEMA_REGISTRY="schema_registry"; POLICY_REGISTRY="policy_registry"; SKILL_REGISTRY="skill_registry"; TOOL_REGISTRY="tool_registry"; PLUGIN_REGISTRY="plugin_registry"; ARTIFACT_REGISTRY="artifact_registry"; RESOURCE_REGISTRY="resource_registry"; UNKNOWN="unknown"
class NameState(str, Enum):
    """名称状态：表达名称生命周期；UNKNOWN 表示状态未知。"""
    RESERVED="reserved"; ACTIVE="active"; ALIASED="aliased"; DEPRECATED="deprecated"; REVOKED="revoked"; ARCHIVED="archived"; UNKNOWN="unknown"
@dataclass(frozen=True, slots=True)
class NamespaceRef:
    """命名空间引用。作用：表达名字所属的命名域；所属 L0 边界：只保存 namespace_id 与 kind；不能解析名称。字段：value 为 namespace_id。"""
    value: RefId; kind: NamespaceKind=NamespaceKind.UNKNOWN; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("NamespaceRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class NameRef:
    """名称引用。作用：表达对象、事件、指标、策略、能力、工具、插件或产物的稳定名称引用；所属 L0 边界：只保存 name_id 与 local_name；不能查询目录。字段：local_name 为局部名称。"""
    value: RefId; local_name: str=""; namespace_ref: NamespaceRef|None=None; state: NameState=NameState.UNKNOWN; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("NameRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class QualifiedName:
    """全限定名。作用：表达带命名空间的全限定名值对象；所属 L0 边界：只保存 namespace 与 name 文本；不能解析对象。字段：namespace 为命名域文本；name 为名称文本。"""
    namespace: str=""; name: str=""; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("QualifiedName.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class RegistryRef:
    """登记边界引用。作用：表达负责登记、解析或治理某类名称的登记边界引用；所属 L0 边界：只保存 registry_id 与 kind；不能执行登记或解析。字段：value 为登记边界引用 ID。"""
    value: RefId; kind: RegistryKind=RegistryKind.UNKNOWN; namespace_ref: NamespaceRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("RegistryRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class NameBindingRef:
    """名称绑定引用。作用：表达名称与 Ref 的绑定事实；所属 L0 边界：只保存 binding_id、name_ref 与 target_ref；不能处理冲突。字段：target_ref 为目标引用。"""
    value: RefId; name_ref: NameRef|None=None; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("NameBindingRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class AliasRef:
    """别名引用。作用：表达别名引用事实；所属 L0 边界：只保存 alias_id、alias_name 与 target_name_ref；不能替换名称。字段：alias_name 为别名文本。"""
    value: RefId; alias_name: str=""; target_name_ref: NameRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("AliasRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class DeprecationRef:
    """名称弃用引用。作用：表达名称或绑定被弃用的事实引用；所属 L0 边界：只保存 deprecation_id 与 target_ref；不能清理名称。字段：value 为弃用引用 ID。"""
    value: RefId; target_ref: TypedRef|None=None; replacement_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("DeprecationRef.schema_version cannot be empty")
