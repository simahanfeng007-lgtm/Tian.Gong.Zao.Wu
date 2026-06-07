"""L1 自我迭代端口协议。

本模块在 L1 中的职责：定义迭代候选、补丁意图、迭代复核、回滚提示、迭代证据和迭代边界协议。
本模块定义哪些端口：IterationCandidatePort、IterationPatchIntentPort、IterationReviewPort、IterationRollbackHintPort、IterationEvidencePort、IterationBoundaryPort。
本模块不实现哪些能力：不生成真实补丁、不修改文件、不合入代码、不执行回滚、不真实审核。
本模块禁止事项：不得访问文件、数据库、网络、真实代码系统、真实模型系统、真实工具系统或插件系统。
本模块与 L2-L6 的关系：L2 可记录迭代状态，L3 可编排候选流，L4 可实现外部适配，L5 可隔离插件迭代边界，L6 可提交子系统迭代候选。
本模块如何服务工程生命体：把模型修正提示、Skill 缺口、工具组缺口和测试补强需求转为候选。
本模块如何保证学习 / 迭代 / 进化不绕过边界：迭代只提交候选、意图、证据和提示，不直接修改系统。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.learning import ImprovementProposalRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.relation import RelationRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import TestRef, ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import PortBoundaryContext, QueryEnvelope
from .learning_ports import LearningCandidate
from .model_feedback_ports import ModelCorrectionHint, ModelSkillGapFeedback, ModelToolNeedFeedback
from .model_reflection_ports import ModelIterationHint, ModelOutcomeAssessment
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult
from .skill_evolution_ports import SkillCorrectionHint, SkillIterationHint
from .tool_gap_ports import ToolFunctionMismatchReport, ToolGroupGapReport, ToolNeedReport


@dataclass(frozen=True, slots=True)
class IterationCandidate:
    """迭代候选对象。

    作用：表达 Skill 流程修订、工具组绑定调整、边界说明修订或测试补强候选。
    边界：不生成补丁，不修改文件，不合入代码。
    """

    candidate_ref: ResourceRef
    proposal_ref: ImprovementProposalRef | None = None
    skill_ref: SkillRef | None = None
    tool_ref: ToolRef | None = None
    relation_ref: RelationRef | None = None
    model_correction_hint: ModelCorrectionHint | None = None
    learning_candidate: LearningCandidate | None = None
    model_iteration_hint: ModelIterationHint | None = None
    skill_iteration_hint: SkillIterationHint | None = None
    tool_need_report: ToolNeedReport | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationPatchIntent:
    """迭代补丁意图对象。

    作用：表达某个候选可能需要补丁、文档修订或协议说明调整的意图。
    边界：不生成 patch，不改源码，不写文件。
    """

    intent_ref: ResourceRef
    candidate: IterationCandidate | None = None
    skill_correction_hint: SkillCorrectionHint | None = None
    model_iteration_hint: ModelIterationHint | None = None
    target_schema_ref: SchemaRef | None = None
    target_version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationReview:
    """迭代复核对象。

    作用：表达迭代候选需要复核、验证、降级或转交后续阶段的事实。
    边界：不真实审核，不批准，不拒绝，不合入。
    """

    candidate: IterationCandidate
    review_ref: ResourceRef | None = None
    outcome_assessment: ModelOutcomeAssessment | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationRollbackHint:
    """迭代回滚提示对象。

    作用：表达某个迭代候选若失败可能需要回退的提示引用。
    边界：不执行回滚，不恢复文件，不修改版本。
    """

    hint_ref: ResourceRef
    candidate_ref: ResourceRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationEvidence:
    """迭代证据对象。

    作用：表达迭代候选依据的测试、验证、模型反馈和缺口报告引用。
    边界：不生成测试报告，不写审计库，不执行验证。
    """

    candidate_ref: ResourceRef | None = None
    test_refs: tuple[TestRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    model_skill_gap_feedback: ModelSkillGapFeedback | None = None
    model_tool_need_feedback: ModelToolNeedFeedback | None = None
    tool_group_gap_report: ToolGroupGapReport | None = None
    tool_function_mismatch_report: ToolFunctionMismatchReport | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationBoundary:
    """迭代边界对象。

    作用：表达迭代候选适用范围、策略引用、风险视图和越界事实。
    边界：不绕过边界，不提升权限，不直接修改系统。
    """

    candidate_ref: ResourceRef | None = None
    boundary: PortBoundary | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    risk_view: RiskView | None = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationCandidateRequest:
    """迭代候选请求。作用：提交迭代候选；边界：不修改系统。"""

    candidate: IterationCandidate
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationCandidateResponse:
    """迭代候选响应。作用：返回迭代候选和证据引用；边界：不合入代码。"""

    candidate: IterationCandidate
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationPatchIntentRequest:
    """迭代补丁意图请求。作用：提交补丁意图；边界：不生成补丁。"""

    intent: IterationPatchIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationPatchIntentResponse:
    """迭代补丁意图响应。作用：返回补丁意图和验证引用；边界：不写文件。"""

    intent: IterationPatchIntent
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationReviewRequest:
    """迭代复核请求。作用：提交复核请求；边界：不批准合入。"""

    review: IterationReview
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationReviewResponse:
    """迭代复核响应。作用：返回复核引用和越界事实；边界：不真实审核。"""

    review: IterationReview
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationRollbackHintRequest:
    """迭代回滚提示请求。作用：提交回滚提示；边界：不执行回滚。"""

    hint: IterationRollbackHint
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationRollbackHintResponse:
    """迭代回滚提示响应。作用：返回回滚提示和验证引用；边界：不恢复版本。"""

    hint: IterationRollbackHint
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationEvidenceRequest:
    """迭代证据请求。作用：提交迭代证据引用；边界：不执行测试。"""

    evidence: IterationEvidence
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationEvidenceResponse:
    """迭代证据响应。作用：返回迭代证据和审计引用；边界：不写审计库。"""

    evidence: IterationEvidence
    audit_ref: AuditRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationBoundaryRequest:
    """迭代边界请求。作用：声明迭代边界；边界：不提升权限。"""

    boundary: IterationBoundary
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationBoundaryResponse:
    """迭代边界响应。作用：返回迭代边界和越界事实；边界：不修改系统。"""

    boundary: IterationBoundary
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class IterationCandidatePort(ABC):
    """迭代候选端口。

    中文名称：迭代候选端口。
    端口职责：定义自我迭代候选提交协议。
    输入输出边界：输入 IterationCandidateRequest 与 TraceContext，输出 PortResult 包装的 IterationCandidateResponse。
    所属 L1 层：自我迭代协议入口。
    不承担的实现职责：不生成补丁，不修改文件，不合入代码。
    如何服务大模型执行力：让模型反馈可转为小步改进候选。
    如何维持绝对边界：候选必须等待后续验证和复核。
    与后续 L2-L6 的关系：后续层可接入状态记录、验证和适配。
    """

    @abstractmethod
    def submit_iteration_candidate(
        self, request: IterationCandidateRequest, trace: TraceContext
    ) -> PortResult[IterationCandidateResponse]:
        """声明迭代候选协议。"""
        raise NotImplementedError


class IterationPatchIntentPort(ABC):
    """迭代补丁意图端口。

    中文名称：迭代补丁意图端口。
    端口职责：定义补丁或修订意图协议。
    输入输出边界：输入 IterationPatchIntentRequest 与 TraceContext，输出 PortResult 包装的 IterationPatchIntentResponse。
    所属 L1 层：自我迭代协议入口。
    不承担的实现职责：不生成 patch，不改源码，不写文件。
    如何服务大模型执行力：让模型可表达需要修正的最小对象。
    如何维持绝对边界：意图不具备写入能力。
    与后续 L2-L6 的关系：后续层可实现验证、候选晋升和合入治理。
    """

    @abstractmethod
    def submit_iteration_patch_intent(
        self, request: IterationPatchIntentRequest, trace: TraceContext
    ) -> PortResult[IterationPatchIntentResponse]:
        """声明迭代补丁意图协议。"""
        raise NotImplementedError


class IterationReviewPort(ABC):
    """迭代复核端口。

    中文名称：迭代复核端口。
    端口职责：定义迭代候选复核请求协议。
    输入输出边界：输入 IterationReviewRequest 与 TraceContext，输出 PortResult 包装的 IterationReviewResponse。
    所属 L1 层：自我迭代协议入口。
    不承担的实现职责：不真实审核，不批准，不拒绝，不合入。
    如何服务大模型执行力：把改进候选纳入受控复核链。
    如何维持绝对边界：复核协议不直接改变系统。
    与后续 L2-L6 的关系：后续层可接入验证、决策和审计。
    """

    @abstractmethod
    def submit_iteration_review(
        self, request: IterationReviewRequest, trace: TraceContext
    ) -> PortResult[IterationReviewResponse]:
        """声明迭代复核协议。"""
        raise NotImplementedError


class IterationRollbackHintPort(ABC):
    """迭代回滚提示端口。

    中文名称：迭代回滚提示端口。
    端口职责：定义迭代失败时可能需要回退的提示协议。
    输入输出边界：输入 IterationRollbackHintRequest 与 TraceContext，输出 PortResult 包装的 IterationRollbackHintResponse。
    所属 L1 层：自我迭代协议入口。
    不承担的实现职责：不执行回滚，不恢复文件，不修改版本。
    如何服务大模型执行力：让模型在改进前保留安全退出提示。
    如何维持绝对边界：提示必须等待后续回退验证协议。
    与后续 L2-L6 的关系：后续层可接入回退验证和版本治理。
    """

    @abstractmethod
    def submit_iteration_rollback_hint(
        self, request: IterationRollbackHintRequest, trace: TraceContext
    ) -> PortResult[IterationRollbackHintResponse]:
        """声明迭代回滚提示协议。"""
        raise NotImplementedError


class IterationEvidencePort(ABC):
    """迭代证据端口。

    中文名称：迭代证据端口。
    端口职责：定义迭代候选的证据引用协议。
    输入输出边界：输入 IterationEvidenceRequest 与 TraceContext，输出 PortResult 包装的 IterationEvidenceResponse。
    所属 L1 层：自我迭代协议入口。
    不承担的实现职责：不生成测试报告，不写审计库，不执行验证。
    如何服务大模型执行力：让迭代候选具备可追踪依据。
    如何维持绝对边界：证据引用不等于执行验证。
    与后续 L2-L6 的关系：后续层可接入测试、验证和审计。
    """

    @abstractmethod
    def attach_iteration_evidence(
        self, request: IterationEvidenceRequest, trace: TraceContext
    ) -> PortResult[IterationEvidenceResponse]:
        """声明迭代证据协议。"""
        raise NotImplementedError


class IterationBoundaryPort(ABC):
    """迭代边界端口。

    中文名称：迭代边界端口。
    端口职责：定义迭代候选边界说明协议。
    输入输出边界：输入 IterationBoundaryRequest 与 TraceContext，输出 PortResult 包装的 IterationBoundaryResponse。
    所属 L1 层：自我迭代协议入口。
    不承担的实现职责：不绕过边界，不提升权限，不直接修改系统。
    如何服务大模型执行力：让模型理解迭代候选可做和不可做的范围。
    如何维持绝对边界：边界说明不是执行许可。
    与后续 L2-L6 的关系：后续层可接入策略、验证和插件隔离。
    """

    @abstractmethod
    def describe_iteration_boundary(
        self, request: IterationBoundaryRequest, trace: TraceContext
    ) -> PortResult[IterationBoundaryResponse]:
        """声明迭代边界协议。"""
        raise NotImplementedError
