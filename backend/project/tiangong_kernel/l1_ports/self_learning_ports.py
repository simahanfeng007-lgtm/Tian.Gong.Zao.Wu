"""L1 自我学习端口协议。

本模块在 L1 中的职责：定义自我学习候选、知识摄入意图、Skill 学习提示、自学证据、自学复核和自学边界协议。
本模块定义哪些端口：SelfLearningCandidatePort、KnowledgeIngestionIntentPort、SkillLearningHintPort、SelfLearningEvidencePort、SelfLearningReviewPort、SelfLearningBoundaryPort。
本模块不实现哪些能力：不启动自学流程、不联网学习、不读文件学习、不写知识库、不生成知识对象、不修改 Skill。
本模块禁止事项：不得访问文件、数据库、网络、真实知识系统、真实模型系统、真实工具系统或插件系统。
本模块与 L2-L6 的关系：L2 可记录自学候选状态，L3 可编排候选流，L4 可实现外部适配，L5 可隔离插件自学范围，L6 可提交子系统自学候选。
本模块如何服务工程生命体：把模型反馈、缺口报告和学习意图转化为可复核自学候选。
本模块如何保证学习 / 迭代 / 进化不绕过边界：自学只提交候选、意图、证据和复核请求，不直接改变知识或 Skill。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.content import ContentRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.learning import LearningRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import PortBoundaryContext, QueryEnvelope
from .learning_ports import LearningCandidate, LearningEvidence, LearningIntent
from .model_feedback_ports import ModelLearningIntent, ModelSkillGapFeedback
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult
from .skill_evolution_ports import SkillEvolutionHint
from .tool_gap_ports import SkillGapReport, ToolNeedReport


@dataclass(frozen=True, slots=True)
class SelfLearningCandidate:
    """自我学习候选对象。

    作用：表达系统可能需要自学补强的候选主题、Skill 或工具需求。
    边界：不启动自学流程，不读取资料，不写知识库。
    """

    candidate_ref: ResourceRef
    learning_intent: LearningIntent | None = None
    model_learning_intent: ModelLearningIntent | None = None
    learning_candidate: LearningCandidate | None = None
    skill_gap_report: SkillGapReport | None = None
    tool_need_report: ToolNeedReport | None = None
    scope_ref: ScopeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class KnowledgeIngestionIntent:
    """知识摄入意图对象。

    作用：表达某些内容、证据或学习结果可能需要进入知识候选流程。
    边界：不摄入真实知识，不写数据库，不生成知识对象。
    """

    intent_ref: ResourceRef
    learning_ref: LearningRef
    learning_intent: LearningIntent | None = None
    model_learning_intent: ModelLearningIntent | None = None
    content_refs: tuple[ContentRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillLearningHint:
    """Skill 学习提示对象。

    作用：表达某个 Skill 需要补充知识、流程或边界说明的学习提示。
    边界：不修改 Skill，不生成 Skill 新版本，不合入知识。
    """

    skill_ref: SkillRef
    skill_gap_feedback: ModelSkillGapFeedback | None = None
    skill_gap_report: SkillGapReport | None = None
    skill_evolution_hint: SkillEvolutionHint | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    version_ref: VersionRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SelfLearningEvidence:
    """自学证据对象。

    作用：表达自学候选所依据的证据、学习证据和验证引用。
    边界：不生成证据，不复制证据，不写证据库。
    """

    candidate_ref: ResourceRef
    learning_ref: LearningRef | None = None
    learning_evidence: LearningEvidence | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SelfLearningReview:
    """自学复核对象。

    作用：表达自学候选是否需要复核、验证或降级的请求事实。
    边界：不执行真实复核，不批准合入，不拒绝候选。
    """

    candidate: SelfLearningCandidate
    review_ref: ResourceRef | None = None
    audit_ref: AuditRef | None = None
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SelfLearningBoundary:
    """自学边界对象。

    作用：表达自学候选的适用范围、风险视图和禁止范围。
    边界：不绕过控制面边界，不触发真实学习，不提升权限。
    """

    candidate_ref: ResourceRef | None = None
    boundary: PortBoundary | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    risk_view: RiskView | None = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SelfLearningCandidateRequest:
    """自我学习候选请求。作用：提交自学候选；边界：不启动自学流程。"""

    candidate: SelfLearningCandidate
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SelfLearningCandidateResponse:
    """自我学习候选响应。作用：返回自学候选和证据引用；边界：不写知识库。"""

    candidate: SelfLearningCandidate
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class KnowledgeIngestionIntentRequest:
    """知识摄入意图请求。作用：提交知识摄入候选；边界：不摄入真实知识。"""

    intent: KnowledgeIngestionIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class KnowledgeIngestionIntentResponse:
    """知识摄入意图响应。作用：返回知识摄入意图和验证引用；边界：不生成知识对象。"""

    intent: KnowledgeIngestionIntent
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillLearningHintRequest:
    """Skill 学习提示请求。作用：提交 Skill 学习补强提示；边界：不修改 Skill。"""

    hint: SkillLearningHint
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillLearningHintResponse:
    """Skill 学习提示响应。作用：返回 Skill 学习提示和证据；边界：不生成新版本。"""

    hint: SkillLearningHint
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SelfLearningEvidenceRequest:
    """自学证据请求。作用：提交自学证据引用；边界：不生成证据。"""

    evidence: SelfLearningEvidence
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SelfLearningEvidenceResponse:
    """自学证据响应。作用：返回自学证据和验证引用；边界：不复制证据。"""

    evidence: SelfLearningEvidence
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SelfLearningReviewRequest:
    """自学复核请求。作用：提交自学候选复核；边界：不批准合入。"""

    review: SelfLearningReview
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SelfLearningReviewResponse:
    """自学复核响应。作用：返回复核引用和越界事实；边界：不执行真实复核。"""

    review: SelfLearningReview
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SelfLearningBoundaryRequest:
    """自学边界请求。作用：声明自学边界；边界：不启动学习。"""

    boundary: SelfLearningBoundary
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SelfLearningBoundaryResponse:
    """自学边界响应。作用：返回自学边界和越界事实；边界：不绕过控制面。"""

    boundary: SelfLearningBoundary
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class SelfLearningCandidatePort(ABC):
    """自我学习候选端口。

    中文名称：自我学习候选端口。
    端口职责：定义自学候选提交协议。
    输入输出边界：输入 SelfLearningCandidateRequest 与 TraceContext，输出 PortResult 包装的 SelfLearningCandidateResponse。
    所属 L1 层：自我学习候选协议入口。
    不承担的实现职责：不启动自学流程，不读资料，不写知识库。
    如何服务大模型执行力：让模型反馈与缺口可转为自学候选。
    如何维持绝对边界：候选不等于真实学习动作。
    与后续 L2-L6 的关系：后续层可接入验证、复核和适配。
    """

    @abstractmethod
    def submit_self_learning_candidate(
        self, request: SelfLearningCandidateRequest, trace: TraceContext
    ) -> PortResult[SelfLearningCandidateResponse]:
        """声明自我学习候选协议。"""
        raise NotImplementedError


class KnowledgeIngestionIntentPort(ABC):
    """知识摄入意图端口。

    中文名称：知识摄入意图端口。
    端口职责：定义知识摄入候选意图协议。
    输入输出边界：输入 KnowledgeIngestionIntentRequest 与 TraceContext，输出 PortResult 包装的 KnowledgeIngestionIntentResponse。
    所属 L1 层：自我学习候选协议入口。
    不承担的实现职责：不摄入知识，不写数据库，不生成知识对象。
    如何服务大模型执行力：让知识缺口可被结构化表达。
    如何维持绝对边界：摄入意图必须等待后续复核。
    与后续 L2-L6 的关系：后续层可实现知识适配与治理。
    """

    @abstractmethod
    def submit_knowledge_ingestion_intent(
        self, request: KnowledgeIngestionIntentRequest, trace: TraceContext
    ) -> PortResult[KnowledgeIngestionIntentResponse]:
        """声明知识摄入意图协议。"""
        raise NotImplementedError


class SkillLearningHintPort(ABC):
    """Skill 学习提示端口。

    中文名称：Skill 学习提示端口。
    端口职责：定义 Skill 学习补强提示协议。
    输入输出边界：输入 SkillLearningHintRequest 与 TraceContext，输出 PortResult 包装的 SkillLearningHintResponse。
    所属 L1 层：自我学习候选协议入口。
    不承担的实现职责：不修改 Skill，不生成版本，不合入知识。
    如何服务大模型执行力：让 Skill 不足可进入学习候选链。
    如何维持绝对边界：提示不触发真实 Skill 修改。
    与后续 L2-L6 的关系：后续层可连接 Skill 演化和验证流程。
    """

    @abstractmethod
    def submit_skill_learning_hint(
        self, request: SkillLearningHintRequest, trace: TraceContext
    ) -> PortResult[SkillLearningHintResponse]:
        """声明 Skill 学习提示协议。"""
        raise NotImplementedError


class SelfLearningEvidencePort(ABC):
    """自学证据端口。

    中文名称：自学证据端口。
    端口职责：定义自学候选证据引用协议。
    输入输出边界：输入 SelfLearningEvidenceRequest 与 TraceContext，输出 PortResult 包装的 SelfLearningEvidenceResponse。
    所属 L1 层：自我学习候选协议入口。
    不承担的实现职责：不生成证据，不复制证据，不写证据库。
    如何服务大模型执行力：让自学候选具备可追踪依据。
    如何维持绝对边界：证据引用不等于证据访问。
    与后续 L2-L6 的关系：后续层可接入验证和审计。
    """

    @abstractmethod
    def attach_self_learning_evidence(
        self, request: SelfLearningEvidenceRequest, trace: TraceContext
    ) -> PortResult[SelfLearningEvidenceResponse]:
        """声明自学证据协议。"""
        raise NotImplementedError


class SelfLearningReviewPort(ABC):
    """自学复核端口。

    中文名称：自学复核端口。
    端口职责：定义自学候选复核请求协议。
    输入输出边界：输入 SelfLearningReviewRequest 与 TraceContext，输出 PortResult 包装的 SelfLearningReviewResponse。
    所属 L1 层：自我学习候选协议入口。
    不承担的实现职责：不真实复核，不批准，不拒绝，不合入。
    如何服务大模型执行力：让自学候选进入受控复核路径。
    如何维持绝对边界：复核协议不直接改变系统。
    与后续 L2-L6 的关系：后续层可接入验证、决策和记录。
    """

    @abstractmethod
    def submit_self_learning_review(
        self, request: SelfLearningReviewRequest, trace: TraceContext
    ) -> PortResult[SelfLearningReviewResponse]:
        """声明自学复核协议。"""
        raise NotImplementedError


class SelfLearningBoundaryPort(ABC):
    """自学边界端口。

    中文名称：自学边界端口。
    端口职责：定义自学候选的范围、风险和越界事实协议。
    输入输出边界：输入 SelfLearningBoundaryRequest 与 TraceContext，输出 PortResult 包装的 SelfLearningBoundaryResponse。
    所属 L1 层：自我学习候选协议入口。
    不承担的实现职责：不绕过边界，不触发真实学习，不提升权限。
    如何服务大模型执行力：让模型理解自学候选的可用范围。
    如何维持绝对边界：边界说明不是执行许可。
    与后续 L2-L6 的关系：后续层可接入控制面、策略和插件隔离。
    """

    @abstractmethod
    def describe_self_learning_boundary(
        self, request: SelfLearningBoundaryRequest, trace: TraceContext
    ) -> PortResult[SelfLearningBoundaryResponse]:
        """声明自学边界协议。"""
        raise NotImplementedError
