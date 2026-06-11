"""L1 第八阶段统一候选端口协议。

本模块在 L1 中的职责：收束学习候选、迭代候选、进化候选，定义候选引用、来源、证据、边界、复核意图、生命周期提示、晋升提示和拒绝提示协议。
本模块定义哪些端口：CandidateReferencePort、CandidateSourcePort、CandidateEvidencePort、CandidateBoundaryPort、CandidateReviewIntentPort、CandidateLifecycleHintPort、CandidatePromotionHintPort、CandidateRejectionHintPort。
本模块不实现哪些能力：不创建真实候选池、不写数据库、不自动生成候选、不采集证据、不做裁决、不复核、不晋升、不删除候选。
本模块禁止事项：不得访问文件、数据库、网络、模型、工具、插件或真实候选系统。
本模块与 L2-L6 的关系：L2 可记录候选状态，L3 可编排候选流，L4 可实现外部存储适配，L5 可隔离插件候选，L6 可提交学习、迭代、进化候选。
本模块如何服务工程生命体：把模型反思、Skill 缺口、工具缺口、观察异常、用户要求和测试失败收束成候选协议。
本模块如何维持大模型执行力与绝对边界：候选只作为证据链入口，不直接修改系统。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.decision import Decision
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef

from .envelope import PortBoundaryContext
from .evolution_ports import EvolutionCandidate
from .learning_ports import LearningCandidate, LearningEvidence
from .model_reflection_ports import ModelFailureFeedback, ModelReflection
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult
from .self_iteration_ports import IterationCandidate, IterationEvidence
from .tool_gap_ports import SkillGapReport, ToolGroupGapReport, ToolNeedReport

@dataclass(frozen=True, slots=True)
class CandidateReference:
    """候选引用对象。作用：表达候选引用；边界：不创建真实候选池。"""
    candidate_ref: ResourceRef
    source_ref: ResourceRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateSource:
    """候选来源对象。作用：表达候选来源；边界：不自动生成候选。"""
    source_ref: ResourceRef
    model_reflection: ModelReflection | None = None
    failure_feedback: ModelFailureFeedback | None = None
    skill_gap_report: SkillGapReport | None = None
    tool_need_report: ToolNeedReport | None = None
    tool_group_gap_report: ToolGroupGapReport | None = None
    observation_ref: ObservationRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateEvidence:
    """候选证据对象。作用：表达候选证据引用；边界：不采集证据、不验证证据。"""
    candidate_ref: ResourceRef
    learning_evidence: LearningEvidence | None = None
    iteration_evidence: IterationEvidence | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateBoundary:
    """候选边界对象。作用：表达候选边界；边界：不做真实裁决。"""
    candidate_ref: ResourceRef
    boundary: PortBoundary | None = None
    risk_view: RiskView | None = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateReviewIntent:
    """候选复核意图对象。作用：表达候选复核意图；边界：不执行复核。"""
    candidate_ref: ResourceRef
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    decision: Decision | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateLifecycleHint:
    """候选生命周期提示对象。作用：表达候选生命周期提示；边界：不改变真实状态。"""
    candidate_ref: ResourceRef
    state_hint: str = "draft"
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidatePromotionHint:
    """统一候选晋升提示对象。

    作用：同时承载学习候选、迭代候选和进化候选的晋升提示。
    边界：只表达候选可进入复核或晋升链，不真实晋升、不合入、不修改系统。
    """
    candidate_ref: ResourceRef
    learning_candidate: LearningCandidate | None = None
    iteration_candidate: IterationCandidate | None = None
    evolution_candidate: EvolutionCandidate | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateRejectionHint:
    """候选拒绝提示对象。作用：表达候选拒绝提示；边界：不删除候选。"""
    candidate_ref: ResourceRef
    reason_ref: ResourceRef | None = None
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateReferenceRequest:
    """CandidateReference请求。作用：提交CandidateReference；边界：只声明候选协议。"""
    payload: CandidateReference
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateSourceRequest:
    """CandidateSource请求。作用：提交CandidateSource；边界：只声明候选协议。"""
    payload: CandidateSource
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateEvidenceRequest:
    """CandidateEvidence请求。作用：提交CandidateEvidence；边界：只声明候选协议。"""
    payload: CandidateEvidence
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateBoundaryRequest:
    """CandidateBoundary请求。作用：提交CandidateBoundary；边界：只声明候选协议。"""
    payload: CandidateBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateReviewIntentRequest:
    """CandidateReviewIntent请求。作用：提交CandidateReviewIntent；边界：只声明候选协议。"""
    payload: CandidateReviewIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateLifecycleHintRequest:
    """CandidateLifecycleHint请求。作用：提交CandidateLifecycleHint；边界：只声明候选协议。"""
    payload: CandidateLifecycleHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidatePromotionHintRequest:
    """CandidatePromotionHint请求。作用：提交CandidatePromotionHint；边界：只声明候选协议。"""
    payload: CandidatePromotionHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateRejectionHintRequest:
    """CandidateRejectionHint请求。作用：提交CandidateRejectionHint；边界：只声明候选协议。"""
    payload: CandidateRejectionHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateReferenceResponse:
    """CandidateReference响应。作用：返回CandidateReference；边界：不改变候选状态。"""
    payload: CandidateReference
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateSourceResponse:
    """CandidateSource响应。作用：返回CandidateSource；边界：不改变候选状态。"""
    payload: CandidateSource
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateEvidenceResponse:
    """CandidateEvidence响应。作用：返回CandidateEvidence；边界：不改变候选状态。"""
    payload: CandidateEvidence
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateBoundaryResponse:
    """CandidateBoundary响应。作用：返回CandidateBoundary；边界：不改变候选状态。"""
    payload: CandidateBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateReviewIntentResponse:
    """CandidateReviewIntent响应。作用：返回CandidateReviewIntent；边界：不改变候选状态。"""
    payload: CandidateReviewIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateLifecycleHintResponse:
    """CandidateLifecycleHint响应。作用：返回CandidateLifecycleHint；边界：不改变候选状态。"""
    payload: CandidateLifecycleHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidatePromotionHintResponse:
    """CandidatePromotionHint响应。作用：返回CandidatePromotionHint；边界：不改变候选状态。"""
    payload: CandidatePromotionHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CandidateRejectionHintResponse:
    """CandidateRejectionHint响应。作用：返回CandidateRejectionHint；边界：不改变候选状态。"""
    payload: CandidateRejectionHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

class CandidateReferencePort(ABC):
    """候选引用端口。中文名称：候选引用端口。端口职责：定义候选引用协议。输入输出边界：输入 CandidateReferenceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段候选协议。不承担的实现职责：不创建候选池。如何服务大模型执行力：让模型建议可被引用。如何维持绝对边界：引用不修改系统。与后续 L2-L6 的关系：供候选生命周期引用。"""
    @abstractmethod
    def reference_candidate(self, request: CandidateReferenceRequest, trace: TraceContext) -> PortResult[CandidateReferenceResponse]:
        """声明候选引用端口。"""
        raise NotImplementedError

class CandidateSourcePort(ABC):
    """候选来源端口。中文名称：候选来源端口。端口职责：定义候选来源协议。输入输出边界：输入 CandidateSourceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段候选协议。不承担的实现职责：不自动生成候选。如何服务大模型执行力：保留反思和缺口来源。如何维持绝对边界：来源不是候选合入。与后续 L2-L6 的关系：供学习、迭代、进化候选引用。"""
    @abstractmethod
    def describe_candidate_source(self, request: CandidateSourceRequest, trace: TraceContext) -> PortResult[CandidateSourceResponse]:
        """声明候选来源端口。"""
        raise NotImplementedError

class CandidateEvidencePort(ABC):
    """候选证据端口。中文名称：候选证据端口。端口职责：定义候选证据协议。输入输出边界：输入 CandidateEvidenceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段候选协议。不承担的实现职责：不采集证据。如何服务大模型执行力：让候选依据可追踪。如何维持绝对边界：证据不等于验证通过。与后续 L2-L6 的关系：供验证和审计链引用。"""
    @abstractmethod
    def attach_candidate_evidence(self, request: CandidateEvidenceRequest, trace: TraceContext) -> PortResult[CandidateEvidenceResponse]:
        """声明候选证据端口。"""
        raise NotImplementedError

class CandidateBoundaryPort(ABC):
    """候选边界端口。中文名称：候选边界端口。端口职责：定义候选边界协议。输入输出边界：输入 CandidateBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段候选协议。不承担的实现职责：不做真实裁决。如何服务大模型执行力：说明候选可处理范围。如何维持绝对边界：边界不放行合入。与后续 L2-L6 的关系：供控制面和验证链引用。"""
    @abstractmethod
    def describe_candidate_boundary(self, request: CandidateBoundaryRequest, trace: TraceContext) -> PortResult[CandidateBoundaryResponse]:
        """声明候选边界端口。"""
        raise NotImplementedError

class CandidateReviewIntentPort(ABC):
    """候选复核意图端口。中文名称：候选复核意图端口。端口职责：定义候选复核意图协议。输入输出边界：输入 CandidateReviewIntentRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段候选协议。不承担的实现职责：不执行复核。如何服务大模型执行力：让候选进入复核链。如何维持绝对边界：复核意图不批准候选。与后续 L2-L6 的关系：供候选治理引用。"""
    @abstractmethod
    def submit_candidate_review_intent(self, request: CandidateReviewIntentRequest, trace: TraceContext) -> PortResult[CandidateReviewIntentResponse]:
        """声明候选复核意图端口。"""
        raise NotImplementedError

class CandidateLifecycleHintPort(ABC):
    """候选生命周期提示端口。中文名称：候选生命周期提示端口。端口职责：定义候选生命周期提示协议。输入输出边界：输入 CandidateLifecycleHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段候选协议。不承担的实现职责：不改变真实状态。如何服务大模型执行力：让候选状态可解释。如何维持绝对边界：提示不更改候选池。与后续 L2-L6 的关系：供状态层和候选治理引用。"""
    @abstractmethod
    def submit_candidate_lifecycle_hint(self, request: CandidateLifecycleHintRequest, trace: TraceContext) -> PortResult[CandidateLifecycleHintResponse]:
        """声明候选生命周期提示端口。"""
        raise NotImplementedError

class CandidatePromotionHintPort(ABC):
    """候选晋升提示端口。中文名称：候选晋升提示端口。端口职责：定义候选晋升提示协议。输入输出边界：输入 CandidatePromotionHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段候选协议。不承担的实现职责：不真实晋升、不合入。如何服务大模型执行力：让已验证候选有后续方向。如何维持绝对边界：提示不是合入。与后续 L2-L6 的关系：供晋升验证链引用。"""
    @abstractmethod
    def submit_candidate_promotion_hint(self, request: CandidatePromotionHintRequest, trace: TraceContext) -> PortResult[CandidatePromotionHintResponse]:
        """声明候选晋升提示端口。"""
        raise NotImplementedError

class CandidateRejectionHintPort(ABC):
    """候选拒绝提示端口。中文名称：候选拒绝提示端口。端口职责：定义候选拒绝提示协议。输入输出边界：输入 CandidateRejectionHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段候选协议。不承担的实现职责：不删除候选。如何服务大模型执行力：让失败候选可学习。如何维持绝对边界：拒绝提示不清理数据。与后续 L2-L6 的关系：供学习反馈和候选治理引用。"""
    @abstractmethod
    def submit_candidate_rejection_hint(self, request: CandidateRejectionHintRequest, trace: TraceContext) -> PortResult[CandidateRejectionHintResponse]:
        """声明候选拒绝提示端口。"""
        raise NotImplementedError
