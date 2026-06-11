"""L2 状态目录对象，记录状态对象元信息、状态域目录和 L2 总目录事实。

本模块位于 L2 状态层，只定义静态状态目录的数据结构，服务工程生命体在冻结收口时表达公共对象、状态域、版本和兼容引用。
本模块不扫描文件系统，不动态导入模块，不读取测试目录，不读取构建配置，也不作为构建系统或注册器。
本模块为后续 L3-L6 提供目录化状态输入，但不承担编排、执行、验证、迁移或插件加载职责。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .component_state import L2StateDomain
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


@dataclass(frozen=True, slots=True)
class StateObjectMeta:
    """状态对象元信息。

    作用：记录状态对象名称、模块引用、状态域、阶段、版本、公开性、弃用性、摘要和稳定哈希提示。
    边界：不反射对象，不扫描模块，不校验真实导出。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    object_name: str = ""
    module_ref: TypedRef | None = None
    domain: L2StateDomain = L2StateDomain.UNKNOWN
    phase: str = ""
    version: str = L2_STATE_SCHEMA_VERSION
    public: bool = True
    deprecated: bool = False
    summary: str = ""
    stable_hash_hint: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("StateObjectMeta.version cannot be empty")
        if len(self.object_name) > 128:
            raise ValueError("StateObjectMeta.object_name must be short")
        if len(self.summary) > 512:
            raise ValueError("StateObjectMeta.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("StateObjectMeta.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StateDomainCatalog:
    """状态域目录。

    作用：记录单个状态域下的状态对象元信息、依赖状态域、导出引用和摘要。
    边界：不扫描目录，不计算对象数量，不生成导出。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    catalog_id: TypedRef | None = None
    domain: L2StateDomain = L2StateDomain.UNKNOWN
    state_objects: tuple[StateObjectMeta, ...] = field(default_factory=tuple)
    dependency_domains: tuple[L2StateDomain, ...] = field(default_factory=tuple)
    export_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("StateDomainCatalog.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("StateDomainCatalog.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L2StateCatalog:
    """L2 状态总目录。

    作用：记录 L2 版本、状态域目录、对象数量、公开对象数量、弃用对象数量、兼容引用和创建时间。
    边界：不扫描 Python 文件，不动态导入模块，不读取项目目录，不生成目录内容。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    catalog_id: TypedRef | None = None
    l2_version: str = L2_STATE_SCHEMA_VERSION
    domains: tuple[StateDomainCatalog, ...] = field(default_factory=tuple)
    total_object_count: int = 0
    public_object_count: int = 0
    deprecated_object_count: int = 0
    compatibility_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.l2_version:
            raise ValueError("L2StateCatalog.l2_version cannot be empty")
        if self.total_object_count < 0:
            raise ValueError("L2StateCatalog.total_object_count cannot be negative")
        if self.public_object_count < 0:
            raise ValueError("L2StateCatalog.public_object_count cannot be negative")
        if self.deprecated_object_count < 0:
            raise ValueError("L2StateCatalog.deprecated_object_count cannot be negative")
        if self.public_object_count > self.total_object_count:
            raise ValueError("L2StateCatalog.public_object_count cannot exceed total_object_count")
        if self.deprecated_object_count > self.total_object_count:
            raise ValueError("L2StateCatalog.deprecated_object_count cannot exceed total_object_count")
        if not self.schema_version:
            raise ValueError("L2StateCatalog.schema_version cannot be empty")
