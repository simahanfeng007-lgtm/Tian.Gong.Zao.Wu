"""L1 检索端口协议。

本模块在 L1 中的职责：定义检索意图、查询、结果、证据绑定、检索边界和检索反馈协议。
本模块定义哪些端口：RetrievalIntentPort、RetrievalQueryPort、RetrievalResultPort、RetrievalEvidencePort、RetrievalBoundaryPort、RetrievalFeedbackPort。
本模块不实现哪些能力：不实现真实检索、不搜索文件、不联网、不连接向量库或数据库、不排序聚合结果。
本模块禁止事项：不得访问文件、网络、数据库、模型、工具、插件或真实索引系统。
本模块与 L2-L6 的关系：L2 可记录检索状态，L3 可编排检索意图，L4 可实现适配，L5 可隔离插件检索边界，L6 可提交子系统检索需求。
本模块如何服务工程生命体：把检索需求、证据和反馈纳入可追踪协议，而不是把 RAG 实现写入 L1。
本模块如何保证学习 / 迭代 / 进化不绕过边界：检索只产出候选引用和证据绑定，不能直接学习、修改或合入。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.content import ContentRef
from tiangong_kernel.l0_primitives.context import ContextRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.goal import GoalRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.retrieval import QueryRef, RetrievalEvidenceRef, RetrievalRef, RetrievalResultRef
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef

from .envelope import PortBoundaryContext, QueryEnvelope
from .port_boundary import PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class RetrievalIntent:
    """检索意图对象。

    作用：表达后续层可能需要进行检索的目标、作用域和证据来源。
    边界：不执行真实检索，不访问索引，不联网。
    """

    intent_ref: ResourceRef
    retrieval_ref: RetrievalRef
    query_ref: QueryRef | None = None
    goal_ref: GoalRef | None = None
    context_ref: ContextRef | None = None
    scope_ref: ScopeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalQuery:
    """检索查询对象。

    作用：表达检索查询引用、边界上下文和候选来源。
    边界：不连接数据库，不搜索文件系统，不执行查询算法。
    """

    query_ref: QueryRef
    query_envelope: QueryEnvelope | None = None
    content_refs: tuple[ContentRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """检索结果对象。

    作用：表达检索结果集合引用和相关证据引用。
    边界：不生成真实结果，不排序，不聚合。
    """

    retrieval_ref: RetrievalRef
    result_ref: RetrievalResultRef
    result_content_refs: tuple[ContentRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalEvidence:
    """检索证据绑定对象。

    作用：表达检索过程或结果与 EvidenceRef 的绑定关系。
    边界：不复制证据，不上传证据，不读取证据内容。
    """

    retrieval_evidence_ref: RetrievalEvidenceRef
    retrieval_ref: RetrievalRef | None = None
    evidence_ref: EvidenceRef | None = None
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


RetrievalEvidenceBinding = RetrievalEvidence


@dataclass(frozen=True, slots=True)
class RetrievalBoundary:
    """检索边界对象。

    作用：表达检索作用域、隐私、策略和证据边界。
    边界：不执行权限裁决，不执行隐私过滤，不连接策略系统。
    """

    retrieval_ref: RetrievalRef
    boundary: PortBoundary | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalFeedback:
    """检索反馈对象。

    作用：表达检索质量、缺口、错误来源和改进信号。
    边界：不训练模型，不更新索引，不重新排序。
    """

    feedback_ref: SignalRef
    retrieval_ref: RetrievalRef | None = None
    result_ref: RetrievalResultRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalIntentRequest:
    """检索意图请求。作用：提交检索意图；边界：不执行检索。"""

    intent: RetrievalIntent
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalIntentResponse:
    """检索意图响应。作用：返回检索意图；边界：不返回真实结果。"""

    intent: RetrievalIntent
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalQueryRequest:
    """检索查询请求。作用：提交查询结构；边界：不连接数据库。"""

    query: RetrievalQuery
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalQueryResponse:
    """检索查询响应。作用：返回查询结构；边界：不执行查询。"""

    query: RetrievalQuery
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalResultRequest:
    """检索结果请求。作用：提交结果引用；边界：不生成结果。"""

    result: RetrievalResult
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalResultResponse:
    """检索结果响应。作用：返回结果引用；边界：不排序聚合。"""

    result: RetrievalResult
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalEvidenceRequest:
    """检索证据请求。作用：提交证据绑定；边界：不读取证据。"""

    evidence: RetrievalEvidence
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalEvidenceResponse:
    """检索证据响应。作用：返回证据绑定；边界：不复制证据。"""

    evidence: RetrievalEvidence
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalBoundaryRequest:
    """检索边界请求。作用：提交边界声明；边界：不执行权限裁决。"""

    boundary: RetrievalBoundary
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalBoundaryResponse:
    """检索边界响应。作用：返回边界声明；边界：不执行过滤。"""

    boundary: RetrievalBoundary
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalFeedbackRequest:
    """检索反馈请求。作用：提交质量反馈；边界：不训练模型。"""

    feedback: RetrievalFeedback
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RetrievalFeedbackResponse:
    """检索反馈响应。作用：返回反馈引用；边界：不更新索引。"""

    feedback: RetrievalFeedback
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class RetrievalIntentPort(ABC):
    """检索意图端口。

    中文名称：检索意图端口。
    端口职责：定义检索需求的候选入口。
    输入输出边界：输入 RetrievalIntentRequest 与 TraceContext，输出 PortResult 包装的 RetrievalIntentResponse。
    所属 L1 层：检索协议入口。
    不承担的实现职责：不执行真实检索，不访问索引，不联网。
    如何服务大模型执行力：让模型所需信息可以被结构化表达。
    如何维持绝对边界：检索意图必须等待后续适配和边界检查。
    与后续 L2-L6 的关系：后续层可实现检索状态、适配和子系统需求。
    """

    @abstractmethod
    def submit_retrieval_intent(self, request: RetrievalIntentRequest, trace: TraceContext) -> PortResult[RetrievalIntentResponse]:
        """声明检索意图协议。"""
        raise NotImplementedError


class RetrievalQueryPort(ABC):
    """检索查询端口。

    中文名称：检索查询端口。
    端口职责：定义检索查询结构协议。
    输入输出边界：输入 RetrievalQueryRequest 与 TraceContext，输出 PortResult 包装的 RetrievalQueryResponse。
    所属 L1 层：检索协议入口。
    不承担的实现职责：不执行查询，不搜索文件，不连接数据库。
    如何服务大模型执行力：把模型的信息需求转成可审查查询引用。
    如何维持绝对边界：查询结构不等于查询执行。
    与后续 L2-L6 的关系：后续层可实现检索适配和边界治理。
    """

    @abstractmethod
    def submit_retrieval_query(self, request: RetrievalQueryRequest, trace: TraceContext) -> PortResult[RetrievalQueryResponse]:
        """声明检索查询协议。"""
        raise NotImplementedError


class RetrievalResultPort(ABC):
    """检索结果端口。

    中文名称：检索结果端口。
    端口职责：定义检索结果引用协议。
    输入输出边界：输入 RetrievalResultRequest 与 TraceContext，输出 PortResult 包装的 RetrievalResultResponse。
    所属 L1 层：检索协议入口。
    不承担的实现职责：不生成结果，不排序，不聚合。
    如何服务大模型执行力：让检索结果以引用形式进入观察和上下文链。
    如何维持绝对边界：只传递结果引用，不暴露真实内容。
    与后续 L2-L6 的关系：后续层可实现结果读取和回传模型上下文。
    """

    @abstractmethod
    def declare_retrieval_result(self, request: RetrievalResultRequest, trace: TraceContext) -> PortResult[RetrievalResultResponse]:
        """声明检索结果协议。"""
        raise NotImplementedError


class RetrievalEvidencePort(ABC):
    """检索证据端口。

    中文名称：检索证据端口。
    端口职责：定义检索结果与证据引用的绑定协议。
    输入输出边界：输入 RetrievalEvidenceRequest 与 TraceContext，输出 PortResult 包装的 RetrievalEvidenceResponse。
    所属 L1 层：检索协议入口。
    不承担的实现职责：不复制证据，不上传证据，不读取证据内容。
    如何服务大模型执行力：让模型使用的信息来源可追溯。
    如何维持绝对边界：证据只绑定引用，不释放内容。
    与后续 L2-L6 的关系：后续层可实现审计和验证。
    """

    @abstractmethod
    def bind_retrieval_evidence(self, request: RetrievalEvidenceRequest, trace: TraceContext) -> PortResult[RetrievalEvidenceResponse]:
        """声明检索证据绑定协议。"""
        raise NotImplementedError


class RetrievalBoundaryPort(ABC):
    """检索边界端口。

    中文名称：检索边界端口。
    端口职责：定义检索作用域、隐私和策略边界协议。
    输入输出边界：输入 RetrievalBoundaryRequest 与 TraceContext，输出 PortResult 包装的 RetrievalBoundaryResponse。
    所属 L1 层：检索协议入口。
    不承担的实现职责：不执行权限裁决，不执行隐私过滤。
    如何服务大模型执行力：让模型知道检索请求的可行边界。
    如何维持绝对边界：边界说明不能被检索意图绕过。
    与后续 L2-L6 的关系：后续层可实现具体策略。
    """

    @abstractmethod
    def describe_retrieval_boundary(self, request: RetrievalBoundaryRequest, trace: TraceContext) -> PortResult[RetrievalBoundaryResponse]:
        """声明检索边界协议。"""
        raise NotImplementedError


class RetrievalFeedbackPort(ABC):
    """检索反馈端口。

    中文名称：检索反馈端口。
    端口职责：定义检索质量反馈协议。
    输入输出边界：输入 RetrievalFeedbackRequest 与 TraceContext，输出 PortResult 包装的 RetrievalFeedbackResponse。
    所属 L1 层：检索协议入口。
    不承担的实现职责：不训练模型，不更新索引，不重新排序。
    如何服务大模型执行力：让检索不足可转为后续学习或迭代候选。
    如何维持绝对边界：反馈不直接修改检索系统。
    与后续 L2-L6 的关系：后续层可接入学习、验证和适配流程。
    """

    @abstractmethod
    def submit_retrieval_feedback(self, request: RetrievalFeedbackRequest, trace: TraceContext) -> PortResult[RetrievalFeedbackResponse]:
        """声明检索反馈协议。"""
        raise NotImplementedError
