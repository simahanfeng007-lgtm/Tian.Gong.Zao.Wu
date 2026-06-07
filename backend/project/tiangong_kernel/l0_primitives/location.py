"""L0 位置、地址、URI 和定位引用事实语言原语。

本模块在 L0 中的职责：定义对象、事件、证据、产物、资源或环境的位置引用事实。
本模块只表达：位置、地址、URI、定位器、位置状态和外层解析提示引用。
本模块明确不做：URI 解析、网络访问、路径规范化、文件读写或后端绑定。
禁止事项：不得打开路径，不得访问网络，不得解析真实存储地址。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class LocationKind(str, Enum):
    """位置类别：只表达对象所在位置类型；UNKNOWN 表示类别未知。"""
    ABSTRACT="abstract"; LOCAL="local"; REMOTE="remote"; VIRTUAL="virtual"; SANDBOX="sandbox"; STORAGE="storage"; NETWORK="network"; ENVIRONMENT="environment"; ARTIFACT="artifact"; UNKNOWN="unknown"
class AddressKind(str, Enum):
    """地址类别：只表达可寻址对象的地址形态；UNKNOWN 表示类别未知。"""
    URI="uri"; PATH="path"; OBJECT_KEY="object_key"; CONTENT_ADDRESS="content_address"; SERVICE_ADDRESS="service_address"; REGISTRY_ADDRESS="registry_address"; MEMORY_ADDRESS="memory_address"; UNKNOWN="unknown"
class URIKind(str, Enum):
    """URI 类别：只表达通用资源标识类型；UNKNOWN 表示类别未知。"""
    GENERIC="generic"; HTTP="http"; HTTPS="https"; FILE="file"; URN="urn"; DATA="data"; CUSTOM="custom"; UNKNOWN="unknown"
class LocatorKind(str, Enum):
    """定位器类别：只表达定位或检索对象的引用方式；UNKNOWN 表示类别未知。"""
    DIRECT="direct"; INDIRECT="indirect"; CONTENT_ADDRESSABLE="content_addressable"; REGISTRY_RESOLVED="registry_resolved"; PROVENANCE_RESOLVED="provenance_resolved"; TEMPORARY="temporary"; UNKNOWN="unknown"
class LocationState(str, Enum):
    """位置状态：只表达位置是否已知或可解析；UNKNOWN 表示状态未知。"""
    KNOWN="known"; RESOLVABLE="resolvable"; UNRESOLVED="unresolved"; MOVED="moved"; MISSING="missing"; REVOKED="revoked"; EXPIRED="expired"; UNKNOWN="unknown"
@dataclass(frozen=True, slots=True)
class LocationRef:
    """位置引用。作用：表达对象、事件、证据、产物、资源、环境、插件、上下文或检查点所处的位置引用；所属 L0 边界：只保存 location_id、kind、state；不能访问位置。"""
    value: RefId; kind: LocationKind=LocationKind.UNKNOWN; state: LocationState=LocationState.UNKNOWN; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("LocationRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class AddressRef:
    """地址引用。作用：表达可寻址对象的地址引用；所属 L0 边界：只保存 address_id、kind、location_ref；不能规范化路径或解析后端。"""
    value: RefId; kind: AddressKind=AddressKind.UNKNOWN; location_ref: LocationRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("AddressRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class URIRef:
    """URI 引用。作用：表达符合通用资源标识思想的资源引用；所属 L0 边界：只保存 uri_id、kind、address_ref；不能解析或访问 URI。"""
    value: RefId; kind: URIKind=URIKind.UNKNOWN; address_ref: AddressRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("URIRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class LocatorRef:
    """定位引用。作用：表达用于定位、解析、访问或检索某对象的定位引用；所属 L0 边界：只保存 locator_id、kind、uri_ref；不能执行解析。"""
    value: RefId; kind: LocatorKind=LocatorKind.UNKNOWN; uri_ref: URIRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("LocatorRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class ResolutionHintRef:
    """解析提示引用。作用：表达外层解析时可使用的提示引用；所属 L0 边界：只保存 resolution_hint_id 和 locator_ref；不能执行解析。"""
    value: RefId; locator_ref: LocatorRef|None=None; hint_kind: str="generic"; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.hint_kind: raise ValueError("ResolutionHintRef.hint_kind cannot be empty")
        if not self.schema_version: raise ValueError("ResolutionHintRef.schema_version cannot be empty")
