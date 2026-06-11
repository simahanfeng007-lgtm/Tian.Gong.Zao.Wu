"""L0 结构版本、迁移引用与兼容性事实语言原语。

本模块在 L0 中的职责：定义结构、对象、事件、快照、产物、能力、插件等版本事实。
本模块只表达：版本引用、结构引用、迁移引用、兼容性、弃用、上投与转换引用。
本模块明确不做：结构目录服务、迁移执行、代码生成、格式转换或验证执行。
禁止事项：不得修改历史事实，不得执行数据转换，不得生成代码。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef

class MigrationKind(str, Enum):
    """迁移类别：表达结构变化方式；UNKNOWN 表示迁移方式未知。"""
    UPCAST="upcast"; IN_PLACE_TRANSFORM="in_place_transform"; COPY_AND_TRANSFORM="copy_and_transform"; WEAK_SCHEMA="weak_schema"; VERSIONED_EVENT="versioned_event"; DEPRECATION="deprecation"; UNKNOWN="unknown"
class CompatibilityLevel(str, Enum):
    """兼容等级：表达新旧结构兼容关系；UNKNOWN 表示兼容性未知。"""
    BACKWARD_COMPATIBLE="backward_compatible"; FORWARD_COMPATIBLE="forward_compatible"; FULL_COMPATIBLE="full_compatible"; BREAKING_CHANGE="breaking_change"; UNKNOWN="unknown"
class VersionState(str, Enum):
    """版本状态：表达版本生命周期；UNKNOWN 表示状态未知。"""
    DRAFT="draft"; ACTIVE="active"; DEPRECATED="deprecated"; RETIRED="retired"; MIGRATING="migrating"; ARCHIVED="archived"; UNKNOWN="unknown"

@dataclass(frozen=True, slots=True)
class SchemaVersion:
    """结构版本。作用：表达结构版本值对象；所属 L0 边界：只保存 major、minor、patch；不能验证结构。字段：major/minor/patch 为版本号。"""
    major: int=0; minor: int=1; patch: int=0; schema_version: str="0.1"
    def __post_init__(self)->None:
        if self.major < 0 or self.minor < 0 or self.patch < 0: raise ValueError("SchemaVersion parts cannot be negative")
        if not self.schema_version: raise ValueError("SchemaVersion.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class ObjectVersion:
    """对象版本。作用：表达对象版本值对象；所属 L0 边界：只保存 version_label 与 state；不能管理对象历史。字段：version_label 为版本标识。"""
    version_label: str=""; state: VersionState=VersionState.UNKNOWN; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ObjectVersion.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class SchemaRef:
    """结构引用。作用：表达对象结构定义引用；所属 L0 边界：只保存 schema_id 与 version；不能验证结构内容。字段：value 为 schema_id。"""
    value: RefId; version: SchemaVersion|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("SchemaRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class VersionRef:
    """版本引用。作用：表达对象、结构、事件、快照、产物、能力、插件等版本事实；所属 L0 边界：只保存 version_id 与 target_ref；不能执行版本切换。字段：value 为版本引用 ID。"""
    value: RefId; target_ref: TypedRef|None=None; object_version: ObjectVersion|None=None; schema_ref: SchemaRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("VersionRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class MigrationRef:
    """迁移引用。作用：表达从旧结构到新结构的迁移事实引用；所属 L0 边界：只保存 migration_id、kind、source_ref 与 target_ref；不能执行迁移。字段：kind 为迁移类别。"""
    value: RefId; kind: MigrationKind=MigrationKind.UNKNOWN; source_ref: TypedRef|None=None; target_ref: TypedRef|None=None; compatibility: CompatibilityLevel=CompatibilityLevel.UNKNOWN; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("MigrationRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class DeprecationRef:
    """弃用引用。作用：表达字段、对象、能力或格式被弃用的事实；所属 L0 边界：只保存 deprecation_id 与 target_ref；不能清理旧对象。字段：value 为弃用引用 ID。"""
    value: RefId; target_ref: TypedRef|None=None; replacement_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("DeprecationRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class UpcastRef:
    """上投引用。作用：表达读取旧事实时转换为新语义的引用；所属 L0 边界：只保存 upcast_id 与 migration_ref；不能执行转换。字段：value 为上投引用 ID。"""
    value: RefId; migration_ref: MigrationRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("UpcastRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class TransformRef:
    """转换引用。作用：表达结构转换事实引用；所属 L0 边界：只保存 transform_id 与 migration_ref；不能处理真实数据。字段：value 为转换引用 ID。"""
    value: RefId; migration_ref: MigrationRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("TransformRef.schema_version cannot be empty")
