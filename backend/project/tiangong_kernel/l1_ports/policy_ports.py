"""L1 策略边界端口协议。

本模块在 L1 中的职责：定义策略引用、策略查询、策略边界说明和策略解释端口协议。
本模块定义：PolicyReferencePort、PolicyLookupPort、PolicyBoundaryPort、PolicyExplainPort。
本模块不实现：真实策略引擎、真实策略裁决、文件策略读取、数据库策略查询或远程策略中心连接。
本模块禁止事项：不得访问文件、网络、数据库、后台任务、真实权限系统、真实工具系统或真实模型系统。
本模块与 L2-L6 的关系：L2 可记录策略引用，L3 可声明策略查询，L4 可实现真实策略适配，L5 可隔离插件策略范围，L6 可声明子系统策略边界。
本模块保证边界不是大模型执行障碍：只提供策略引用和范围说明，让后续层获得清晰界限，而不替大模型做策略裁决。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.contract import ContractRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.namespace import NamespaceRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import QueryEnvelope
from .port_boundary import BoundaryHint, BoundaryRule, PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class PolicyBoundary:
    """策略边界对象。

    作用：表达策略适用范围、合同边界、命名空间和证据引用。
    边界：不执行策略匹配，不进行真实裁决，不连接策略系统。
    """

    policy_ref: PolicyRef
    boundary: PortBoundary
    contract_ref: ContractRef | None = None
    scope_ref: ScopeRef | None = None
    namespace_ref: NamespaceRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class PolicyReferenceRequest:
    """策略引用请求。

    作用：声明调用方需要引用某个策略事实。
    边界：不解析策略内容，不判断策略是否允许执行。
    """

    policy_ref: PolicyRef
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    namespace_ref: NamespaceRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class PolicyReferenceResponse:
    """策略引用响应。

    作用：承载策略引用、版本、范围和证据引用。
    边界：不代表策略已加载，不代表裁决已完成。
    """

    policy_ref: PolicyRef
    version_ref: VersionRef | None = None
    scope_ref: ScopeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class PolicyLookupRequest:
    """策略查询请求。

    作用：声明按策略引用、范围和查询信封查找策略说明的协议需求。
    边界：不读文件，不查数据库，不访问远程策略中心。
    """

    policy_ref: PolicyRef | None = None
    query: QueryEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    resource_ref: ResourceRef | None = None
    namespace_ref: NamespaceRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class PolicyLookupResponse:
    """策略查询响应。

    作用：承载查询得到的策略引用集合和验证引用。
    边界：不排序、不打分、不完成真实策略读取。
    """

    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class PolicyBoundaryRequest:
    """策略边界请求。

    作用：声明需要说明某个策略适用范围和边界条件。
    边界：不执行策略裁决，不改变策略状态。
    """

    policy_ref: PolicyRef
    contract_ref: ContractRef | None = None
    scope_ref: ScopeRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class PolicyBoundaryResponse:
    """策略边界响应。

    作用：承载策略边界对象、规则和证据引用。
    边界：不代表策略生效，不代表执行被允许或拒绝。
    """

    boundary: PolicyBoundary
    rules: tuple[BoundaryRule, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class PolicyExplainRequest:
    """策略解释请求。

    作用：声明需要解释的策略引用、边界和查询条件。
    边界：不调用模型，不生成真实自然语言解释，不裁决。
    """

    policy_ref: PolicyRef
    boundary: PolicyBoundary | None = None
    query: QueryEnvelope | None = None
    actor_ref: ActorRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class PolicyExplainResponse:
    """策略解释响应。

    作用：承载策略提示、规则、验证和证据引用。
    边界：只表达解释材料，不调用任何外部解释器。
    """

    hint: BoundaryHint
    policy_ref: PolicyRef
    rules: tuple[BoundaryRule, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class PolicyReferencePort(ABC):
    """策略引用端口。

    中文名称：策略引用端口。
    端口职责：定义 PolicyRef 的引用和返回协议。
    输入输出边界：输入 PolicyReferenceRequest 与 TraceContext，输出 PortResult 包装的 PolicyReferenceResponse。
    所属 L1 层：控制面策略端口协议。
    不承担的实现职责：不加载策略，不裁决策略，不读取外部策略源。
    如何服务大模型执行力：让策略以引用形式进入上下文，避免复杂审批链干扰工作流。
    如何维持绝对边界：策略引用始终保留范围、版本和证据。
    """

    @abstractmethod
    def reference_policy(self, request: PolicyReferenceRequest, trace: TraceContext) -> PortResult[PolicyReferenceResponse]:
        """声明策略引用协议。"""
        raise NotImplementedError


class PolicyLookupPort(ABC):
    """策略查询端口。

    中文名称：策略查询端口。
    端口职责：定义策略查询条件与策略引用集合返回协议。
    输入输出边界：输入 PolicyLookupRequest 与 TraceContext，输出 PortResult 包装的 PolicyLookupResponse。
    所属 L1 层：控制面策略端口协议。
    不承担的实现职责：不读取文件、数据库或远程策略中心。
    如何服务大模型执行力：将策略查找保持为轻量协议，不阻塞后续执行设计。
    如何维持绝对边界：查询结果仍是 PolicyRef，不泄漏真实策略实现。
    """

    @abstractmethod
    def lookup_policy(self, request: PolicyLookupRequest, trace: TraceContext) -> PortResult[PolicyLookupResponse]:
        """声明策略查询协议。"""
        raise NotImplementedError


class PolicyBoundaryPort(ABC):
    """策略边界端口。

    中文名称：策略边界端口。
    端口职责：定义策略适用范围和禁止范围的说明协议。
    输入输出边界：输入 PolicyBoundaryRequest 与 TraceContext，输出 PortResult 包装的 PolicyBoundaryResponse。
    所属 L1 层：控制面策略端口协议。
    不承担的实现职责：不执行真实策略裁决，不改变请求状态。
    如何服务大模型执行力：提供清晰策略边界，降低后续层误判成本。
    如何维持绝对边界：策略范围通过 PortBoundary 和证据引用表达。
    """

    @abstractmethod
    def describe_policy_boundary(self, request: PolicyBoundaryRequest, trace: TraceContext) -> PortResult[PolicyBoundaryResponse]:
        """声明策略边界协议。"""
        raise NotImplementedError

    @abstractmethod
    def current_policy_boundary(self, trace: TraceContext) -> CoreResult[PolicyBoundary]:
        """声明当前策略边界读取协议。"""
        raise NotImplementedError


class PolicyExplainPort(ABC):
    """策略解释端口。

    中文名称：策略解释端口。
    端口职责：定义策略解释材料、规则和提示返回协议。
    输入输出边界：输入 PolicyExplainRequest 与 TraceContext，输出 PortResult 包装的 PolicyExplainResponse。
    所属 L1 层：控制面策略端口协议。
    不承担的实现职责：不调用模型，不生成真实解释，不做裁决。
    如何服务大模型执行力：把策略边界变成可理解材料，而不是不可见阻断。
    如何维持绝对边界：解释材料不改变策略边界本身。
    """

    @abstractmethod
    def explain_policy(self, request: PolicyExplainRequest, trace: TraceContext) -> PortResult[PolicyExplainResponse]:
        """声明策略解释协议。"""
        raise NotImplementedError
