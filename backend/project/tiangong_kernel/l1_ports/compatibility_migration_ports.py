"""L1 第八阶段兼容、迁移、废弃与版本适配端口协议。

本模块在 L1 中的职责：定义兼容检查、版本兼容、端口兼容映射、迁移提示、迁移边界、废弃通知、Schema 迁移边界、向后兼容提示和向前兼容提示协议。
本模块定义哪些端口：CompatibilityCheckPort、VersionCompatibilityPort、PortCompatibilityMapPort、MigrationHintPort、MigrationBoundaryPort、DeprecationNoticePort、SchemaMigrationBoundaryPort、BackwardCompatibilityHintPort、ForwardCompatibilityHintPort。
本模块不实现哪些能力：不执行真实兼容算法、不改版本、不迁移端口、不读写数据、不改配置、不删除旧接口、不实施适配器。
本模块禁止事项：不得访问文件、数据库、网络、模型、工具、插件或旧上层模块。
本模块与 L2-L6 的关系：L2 可记录版本状态，L3 可编排迁移意图，L4 可实现适配器，L5 可约束插件兼容，L6 可声明子系统迁移提示。
本模块如何服务工程生命体：让系统在成长时有可追踪的兼容与迁移边界。
本模块如何维持大模型执行力与绝对边界：兼容提示服务于连续执行，不在 L1 真实迁移。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.contract import ContractRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.namespace import NamespaceRef
from tiangong_kernel.l0_primitives.relation import RelationRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import DeprecationRef, MigrationRef, SchemaRef, TransformRef, UpcastRef, VersionRef

from .envelope import PortBoundaryContext
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult

@dataclass(frozen=True, slots=True)
class CompatibilityCheck:
    """兼容检查对象。作用：表达兼容检查请求事实；边界：不执行真实检查算法。"""
    check_ref: ResourceRef
    source_ref: ResourceRef | None = None
    target_ref: ResourceRef | None = None
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class VersionCompatibility:
    """版本兼容对象。作用：表达版本兼容关系；边界：不改版本。"""
    version_ref: VersionRef
    target_version_ref: VersionRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PortCompatibilityMap:
    """端口兼容映射对象。作用：表达端口兼容映射；边界：不重写端口、不迁移端口。"""
    map_ref: ResourceRef
    source_namespace_ref: NamespaceRef | None = None
    target_namespace_ref: NamespaceRef | None = None
    relation_refs: tuple[RelationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class MigrationHint:
    """迁移提示对象。作用：表达迁移方向；边界：不执行迁移。"""
    migration_ref: MigrationRef
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class MigrationBoundary:
    """迁移边界对象。作用：表达迁移边界；边界：不读写数据、不改配置。"""
    migration_ref: MigrationRef = None
    boundary: PortBoundary | None = None
    contract_ref: ContractRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class DeprecationNotice:
    """废弃通知对象。作用：表达废弃提示；边界：不删除旧接口。"""
    deprecation_ref: DeprecationRef
    replacement_ref: ResourceRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SchemaMigrationBoundary:
    """Schema 迁移边界对象。作用：表达 Schema 迁移边界；边界：不执行 schema 迁移。"""
    schema_ref: SchemaRef
    migration_ref: MigrationRef = None
    transform_ref: TransformRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class BackwardCompatibilityHint:
    """向后兼容提示对象。作用：表达向后兼容要求；边界：不实施兼容层。"""
    hint_ref: ResourceRef
    upcast_ref: UpcastRef | None = None
    version_ref: VersionRef = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ForwardCompatibilityHint:
    """向前兼容提示对象。作用：表达向前兼容要求；边界：不实施适配器。"""
    hint_ref: ResourceRef
    version_ref: VersionRef = None
    schema_ref: SchemaRef = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CompatibilityCheckRequest:
    """CompatibilityCheck请求。作用：提交CompatibilityCheck；边界：只声明兼容迁移协议。"""
    payload: CompatibilityCheck
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class VersionCompatibilityRequest:
    """VersionCompatibility请求。作用：提交VersionCompatibility；边界：只声明兼容迁移协议。"""
    payload: VersionCompatibility
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PortCompatibilityMapRequest:
    """PortCompatibilityMap请求。作用：提交PortCompatibilityMap；边界：只声明兼容迁移协议。"""
    payload: PortCompatibilityMap
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class MigrationHintRequest:
    """MigrationHint请求。作用：提交MigrationHint；边界：只声明兼容迁移协议。"""
    payload: MigrationHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class MigrationBoundaryRequest:
    """MigrationBoundary请求。作用：提交MigrationBoundary；边界：只声明兼容迁移协议。"""
    payload: MigrationBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class DeprecationNoticeRequest:
    """DeprecationNotice请求。作用：提交DeprecationNotice；边界：只声明兼容迁移协议。"""
    payload: DeprecationNotice
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SchemaMigrationBoundaryRequest:
    """SchemaMigrationBoundary请求。作用：提交SchemaMigrationBoundary；边界：只声明兼容迁移协议。"""
    payload: SchemaMigrationBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class BackwardCompatibilityHintRequest:
    """BackwardCompatibilityHint请求。作用：提交BackwardCompatibilityHint；边界：只声明兼容迁移协议。"""
    payload: BackwardCompatibilityHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ForwardCompatibilityHintRequest:
    """ForwardCompatibilityHint请求。作用：提交ForwardCompatibilityHint；边界：只声明兼容迁移协议。"""
    payload: ForwardCompatibilityHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CompatibilityCheckResponse:
    """CompatibilityCheck响应。作用：返回CompatibilityCheck；边界：不执行迁移或适配。"""
    payload: CompatibilityCheck
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class VersionCompatibilityResponse:
    """VersionCompatibility响应。作用：返回VersionCompatibility；边界：不执行迁移或适配。"""
    payload: VersionCompatibility
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PortCompatibilityMapResponse:
    """PortCompatibilityMap响应。作用：返回PortCompatibilityMap；边界：不执行迁移或适配。"""
    payload: PortCompatibilityMap
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class MigrationHintResponse:
    """MigrationHint响应。作用：返回MigrationHint；边界：不执行迁移或适配。"""
    payload: MigrationHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class MigrationBoundaryResponse:
    """MigrationBoundary响应。作用：返回MigrationBoundary；边界：不执行迁移或适配。"""
    payload: MigrationBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class DeprecationNoticeResponse:
    """DeprecationNotice响应。作用：返回DeprecationNotice；边界：不执行迁移或适配。"""
    payload: DeprecationNotice
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SchemaMigrationBoundaryResponse:
    """SchemaMigrationBoundary响应。作用：返回SchemaMigrationBoundary；边界：不执行迁移或适配。"""
    payload: SchemaMigrationBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class BackwardCompatibilityHintResponse:
    """BackwardCompatibilityHint响应。作用：返回BackwardCompatibilityHint；边界：不执行迁移或适配。"""
    payload: BackwardCompatibilityHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ForwardCompatibilityHintResponse:
    """ForwardCompatibilityHint响应。作用：返回ForwardCompatibilityHint；边界：不执行迁移或适配。"""
    payload: ForwardCompatibilityHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

class CompatibilityCheckPort(ABC):
    """兼容检查端口。中文名称：兼容检查端口。端口职责：定义兼容检查协议。输入输出边界：输入 CompatibilityCheckRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段兼容协议。不承担的实现职责：不执行真实检查算法。如何服务大模型执行力：让变更有兼容提示。如何维持绝对边界：检查协议不改系统。与后续 L2-L6 的关系：供版本和迁移链引用。"""
    @abstractmethod
    def request_compatibility_check(self, request: CompatibilityCheckRequest, trace: TraceContext) -> PortResult[CompatibilityCheckResponse]:
        """声明兼容检查端口。"""
        raise NotImplementedError

class VersionCompatibilityPort(ABC):
    """版本兼容端口。中文名称：版本兼容端口。端口职责：定义版本兼容协议。输入输出边界：输入 VersionCompatibilityRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段兼容协议。不承担的实现职责：不改版本。如何服务大模型执行力：保持跨版本理解。如何维持绝对边界：兼容说明不迁移版本。与后续 L2-L6 的关系：供版本治理引用。"""
    @abstractmethod
    def describe_version_compatibility(self, request: VersionCompatibilityRequest, trace: TraceContext) -> PortResult[VersionCompatibilityResponse]:
        """声明版本兼容端口。"""
        raise NotImplementedError

class PortCompatibilityMapPort(ABC):
    """端口兼容映射端口。中文名称：端口兼容映射端口。端口职责：定义端口兼容映射协议。输入输出边界：输入 PortCompatibilityMapRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段兼容协议。不承担的实现职责：不重写端口。如何服务大模型执行力：让后续层迁移时不断链。如何维持绝对边界：映射不替代迁移。与后续 L2-L6 的关系：供迁移和适配器引用。"""
    @abstractmethod
    def describe_port_compatibility_map(self, request: PortCompatibilityMapRequest, trace: TraceContext) -> PortResult[PortCompatibilityMapResponse]:
        """声明端口兼容映射端口。"""
        raise NotImplementedError

class MigrationHintPort(ABC):
    """迁移提示端口。中文名称：迁移提示端口。端口职责：定义迁移提示协议。输入输出边界：输入 MigrationHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段迁移协议。不承担的实现职责：不执行迁移。如何服务大模型执行力：让系统演进有迁移提示。如何维持绝对边界：提示不写数据。与后续 L2-L6 的关系：供外部适配与进化链引用。"""
    @abstractmethod
    def submit_migration_hint(self, request: MigrationHintRequest, trace: TraceContext) -> PortResult[MigrationHintResponse]:
        """声明迁移提示端口。"""
        raise NotImplementedError

class MigrationBoundaryPort(ABC):
    """迁移边界端口。中文名称：迁移边界端口。端口职责：定义迁移边界协议。输入输出边界：输入 MigrationBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段迁移协议。不承担的实现职责：不读写数据、不改配置。如何服务大模型执行力：明确迁移危险边界。如何维持绝对边界：边界不迁移。与后续 L2-L6 的关系：供迁移适配和安全边界引用。"""
    @abstractmethod
    def describe_migration_boundary(self, request: MigrationBoundaryRequest, trace: TraceContext) -> PortResult[MigrationBoundaryResponse]:
        """声明迁移边界端口。"""
        raise NotImplementedError

class DeprecationNoticePort(ABC):
    """废弃通知端口。中文名称：废弃通知端口。端口职责：定义废弃通知协议。输入输出边界：输入 DeprecationNoticeRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段兼容协议。不承担的实现职责：不删除旧接口。如何服务大模型执行力：让模型理解废弃路径。如何维持绝对边界：通知不改接口。与后续 L2-L6 的关系：供迁移和文档层引用。"""
    @abstractmethod
    def submit_deprecation_notice(self, request: DeprecationNoticeRequest, trace: TraceContext) -> PortResult[DeprecationNoticeResponse]:
        """声明废弃通知端口。"""
        raise NotImplementedError

class SchemaMigrationBoundaryPort(ABC):
    """Schema 迁移边界端口。中文名称：Schema 迁移边界端口。端口职责：定义 Schema 迁移边界协议。输入输出边界：输入 SchemaMigrationBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段迁移协议。不承担的实现职责：不执行 schema 迁移。如何服务大模型执行力：保持数据结构可解释。如何维持绝对边界：边界不转换数据。与后续 L2-L6 的关系：供版本和外部适配引用。"""
    @abstractmethod
    def describe_schema_migration_boundary(self, request: SchemaMigrationBoundaryRequest, trace: TraceContext) -> PortResult[SchemaMigrationBoundaryResponse]:
        """声明Schema 迁移边界端口。"""
        raise NotImplementedError

class BackwardCompatibilityHintPort(ABC):
    """向后兼容提示端口。中文名称：向后兼容提示端口。端口职责：定义向后兼容提示协议。输入输出边界：输入 BackwardCompatibilityHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段兼容协议。不承担的实现职责：不实施兼容层。如何服务大模型执行力：保证旧流程可理解。如何维持绝对边界：提示不加载适配。与后续 L2-L6 的关系：供迁移和插件生态引用。"""
    @abstractmethod
    def submit_backward_compatibility_hint(self, request: BackwardCompatibilityHintRequest, trace: TraceContext) -> PortResult[BackwardCompatibilityHintResponse]:
        """声明向后兼容提示端口。"""
        raise NotImplementedError

class ForwardCompatibilityHintPort(ABC):
    """向前兼容提示端口。中文名称：向前兼容提示端口。端口职责：定义向前兼容提示协议。输入输出边界：输入 ForwardCompatibilityHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段兼容协议。不承担的实现职责：不实施适配器。如何服务大模型执行力：让后续扩展不破坏主链。如何维持绝对边界：提示不改变协议。与后续 L2-L6 的关系：供后续层规划引用。"""
    @abstractmethod
    def submit_forward_compatibility_hint(self, request: ForwardCompatibilityHintRequest, trace: TraceContext) -> PortResult[ForwardCompatibilityHintResponse]:
        """声明向前兼容提示端口。"""
        raise NotImplementedError
