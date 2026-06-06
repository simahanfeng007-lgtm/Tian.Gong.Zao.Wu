
"""L1 第八阶段验证、复核、测试与候选验证端口协议。

本模块在 L1 中的职责：定义验证引用、验证请求、复核、测试计划、质量边界、候选验证、学习测试、迭代复核、进化验证、回退验证、恢复验证和候选晋升提示协议。
本模块定义哪些端口：ValidationReferencePort、ValidationRequestPort、VerificationPort、TestReferencePort、TestPlanIntentPort、QualityBoundaryPort、CandidateValidationPort、LearningTestPort、IterationVerificationPort、EvolutionValidationPort、RollbackVerificationPort、RestoreVerificationPort、CandidatePromotionHintPort。
本模块不实现哪些能力：不运行测试、不执行验证器、不调用外部工具、不读取文件、不合入候选、不执行回退或恢复。
本模块禁止事项：不得访问真实文件、数据库、网络、模型、工具、插件或持续集成系统。
本模块与 L2-L6 的关系：L2 可记录验证状态，L3 可编排验证请求，L4 可实现外部验证适配，L5 可约束插件候选，L6 可提交学习、迭代、进化候选验证引用。
本模块如何服务工程生命体：为学习、迭代、进化候选提供可追踪、可复核、可回退验证入口。
本模块如何维持大模型执行力与绝对边界：验证协议只保护高影响候选，不阻碍日常 Skill 与工具组链路。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.decision import Decision
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import TestRef, TestResultRef, ValidationRef, VerificationRef

from .envelope import PortBoundaryContext, QueryEnvelope
from .learning_ports import LearningEvidence, LearningResult
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult
from .self_iteration_ports import IterationCandidate, IterationEvidence, IterationRollbackHint
from .evolution_ports import EvolutionCandidate, EvolutionEvidence, EvolutionRollbackHint


@dataclass(frozen=True, slots=True)
class QualityBoundary:
    """质量边界对象。作用：表达候选或结果需要满足的质量约束；边界：不运行测试、不阻断日常行动。"""
    boundary_ref: ResourceRef
    boundary: PortBoundary | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    test_refs: tuple[TestRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class CandidatePromotionHint:
    """候选晋升提示对象。作用：表达候选可能进入更高复核或发布环节；边界：不真实晋升、不合入、不修改系统。"""
    candidate_ref: ResourceRef
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    decision: Decision | None = None
    risk_view: RiskView | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RollbackVerificationHint:
    """回退验证提示对象。作用：表达回退后需要验证的引用和证据；边界：不执行回退、不恢复状态。"""
    hint_ref: ResourceRef
    rollback_candidate_ref: ResourceRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ValidationReference:
    """验证引用对象。作用：表达验证引用；边界：不执行验证。"""
    validation_ref: ValidationRef
    scope_ref: ScopeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ValidationReferenceRequest:
    """验证引用请求。作用：声明验证引用；边界：不执行验证。"""
    validation_ref: ValidationRef
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ValidationReferenceResponse:
    """验证引用响应。作用：返回验证引用和证据；边界：不读取证据。"""
    validation_ref: ValidationRef
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ValidationRequest:
    """验证请求。作用：表达候选或结果需要被验证；边界：不运行验证器。"""
    validation_ref: ValidationRef
    target_ref: ResourceRef | None = None
    query: QueryEnvelope | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ValidationResponse:
    """验证响应。作用：返回验证引用与边界上下文；边界：不判定真实通过。"""
    validation_ref: ValidationRef
    boundary_context: PortBoundaryContext | None = None
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class VerificationRequest:
    """复核请求。作用：表达复核对象；边界：不执行真实复核算法。"""
    verification_ref: VerificationRef
    target_ref: ResourceRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class VerificationResponse:
    """复核响应。作用：返回复核引用；边界：不批准、不拒绝、不合入。"""
    verification_ref: VerificationRef
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TestReferenceRequest:
    """测试引用请求。作用：声明测试引用；边界：不运行测试。"""
    test_ref: TestRef
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TestReferenceResponse:
    """测试引用响应。作用：返回测试引用；边界：不读取测试文件。"""
    test_ref: TestRef
    result_ref: TestResultRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TestPlanIntentRequest:
    """测试计划意图请求。作用：表达测试计划意图；边界：不生成真实测试计划。"""
    plan_ref: ResourceRef
    test_refs: tuple[TestRef, ...] = field(default_factory=tuple)
    target_ref: ResourceRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TestPlanIntentResponse:
    """测试计划意图响应。作用：返回测试计划引用；边界：不执行测试计划。"""
    plan_ref: ResourceRef
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class QualityBoundaryRequest:
    """质量边界请求。作用：声明质量边界；边界：不阻断日常工具链。"""
    boundary: QualityBoundary
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class QualityBoundaryResponse:
    """质量边界响应。作用：返回质量边界与越界事实；边界：不执行裁决。"""
    boundary: QualityBoundary
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class CandidateValidationRequest:
    """候选验证请求。作用：声明候选进入验证；边界：不验证候选。"""
    candidate_ref: ResourceRef
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class CandidateValidationResponse:
    """候选验证响应。作用：返回候选验证引用；边界：不合入候选。"""
    candidate_ref: ResourceRef
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningTestRequest:
    """学习测试请求。作用：表达学习成果测试意图；边界：不执行学习测试。"""
    learning_result: LearningResult | None = None
    learning_evidence: LearningEvidence | None = None
    test_refs: tuple[TestRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningTestResponse:
    """学习测试响应。作用：返回学习测试引用；边界：不写知识库。"""
    test_refs: tuple[TestRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationVerificationRequest:
    """迭代复核请求。作用：表达迭代候选复核意图；边界：不生成补丁、不合入。"""
    candidate: IterationCandidate | None = None
    evidence: IterationEvidence | None = None
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IterationVerificationResponse:
    """迭代复核响应。作用：返回迭代复核引用；边界：不修改源码。"""
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionValidationRequest:
    """进化验证请求。作用：表达进化候选验证意图；边界：不执行进化。"""
    candidate: EvolutionCandidate | None = None
    evidence: EvolutionEvidence | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionValidationResponse:
    """进化验证响应。作用：返回进化验证引用；边界：不修改架构。"""
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RollbackVerificationRequest:
    """回退验证请求。作用：表达回退结果验证意图；边界：不执行回退。"""
    hint: IterationRollbackHint | EvolutionRollbackHint | RollbackVerificationHint
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RollbackVerificationResponse:
    """回退验证响应。作用：返回回退验证引用；边界：不恢复状态。"""
    hint: IterationRollbackHint | EvolutionRollbackHint | RollbackVerificationHint
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RestoreVerificationRequest:
    """恢复验证请求。作用：表达恢复点恢复结果的验证意图；边界：不恢复任何状态。"""
    restore_ref: ResourceRef
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RestoreVerificationResponse:
    """恢复验证响应。作用：返回恢复验证引用；边界：不创建恢复点。"""
    restore_ref: ResourceRef
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class CandidatePromotionHintRequest:
    """候选晋升提示请求。作用：提交晋升提示；边界：不真实晋升。"""
    hint: CandidatePromotionHint
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class CandidatePromotionHintResponse:
    """候选晋升提示响应。作用：返回晋升提示与验证引用；边界：不合入候选。"""
    hint: CandidatePromotionHint
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class ValidationReferencePort(ABC):
    """验证引用端口。中文名称：验证引用端口。端口职责：定义验证引用协议。输入输出边界：输入 ValidationReferenceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段验证协议。不承担的实现职责：不执行真实验证。如何服务大模型执行力：让模型产出的候选具备验证引用。如何维持绝对边界：引用不是验证通过。与后续 L2-L6 的关系：供状态、编排、适配和子系统验证链引用。"""
    @abstractmethod
    def reference_validation(self, request: ValidationReferenceRequest, trace: TraceContext) -> PortResult[ValidationReferenceResponse]:
        """声明验证引用协议。"""
        raise NotImplementedError


class ValidationRequestPort(ABC):
    """验证请求端口。中文名称：验证请求端口。端口职责：定义验证请求协议。输入输出边界：输入 ValidationRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段验证协议。不承担的实现职责：不运行验证器、不调用工具。如何服务大模型执行力：把候选交给后续验证链而不中断主链。如何维持绝对边界：验证请求不是执行许可。与后续 L2-L6 的关系：供运行编排与子系统候选验证引用。"""
    @abstractmethod
    def request_validation(self, request: ValidationRequest, trace: TraceContext) -> PortResult[ValidationResponse]:
        """声明验证请求协议。"""
        raise NotImplementedError


class VerificationPort(ABC):
    """复核端口。中文名称：复核端口。端口职责：定义复核协议。输入输出边界：输入 VerificationRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段验证协议。不承担的实现职责：不执行复核算法、不批准合入。如何服务大模型执行力：为候选提供复核入口。如何维持绝对边界：复核协议不改变系统。与后续 L2-L6 的关系：供候选复核与审计链引用。"""
    @abstractmethod
    def request_verification(self, request: VerificationRequest, trace: TraceContext) -> PortResult[VerificationResponse]:
        """声明复核协议。"""
        raise NotImplementedError


class TestReferencePort(ABC):
    """测试引用端口。中文名称：测试引用端口。端口职责：定义测试引用协议。输入输出边界：输入 TestReferenceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段测试协议。不承担的实现职责：不运行测试。如何服务大模型执行力：让模型建议可关联测试事实。如何维持绝对边界：测试引用不触发测试执行。与后续 L2-L6 的关系：供验证、质量与候选复核引用。"""
    @abstractmethod
    def reference_test(self, request: TestReferenceRequest, trace: TraceContext) -> PortResult[TestReferenceResponse]:
        """声明测试引用协议。"""
        raise NotImplementedError


class TestPlanIntentPort(ABC):
    """测试计划意图端口。中文名称：测试计划意图端口。端口职责：定义测试计划意图协议。输入输出边界：输入 TestPlanIntentRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段测试协议。不承担的实现职责：不生成真实计划、不运行测试。如何服务大模型执行力：让模型提出验证方向。如何维持绝对边界：计划意图不是执行动作。与后续 L2-L6 的关系：供 L3 编排和 L6 质检子系统引用。"""
    @abstractmethod
    def submit_test_plan_intent(self, request: TestPlanIntentRequest, trace: TraceContext) -> PortResult[TestPlanIntentResponse]:
        """声明测试计划意图协议。"""
        raise NotImplementedError


class QualityBoundaryPort(ABC):
    """质量边界端口。中文名称：质量边界端口。端口职责：定义质量边界说明协议。输入输出边界：输入 QualityBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段质量协议。不承担的实现职责：不阻断日常工具调用。如何服务大模型执行力：仅对高影响候选表达质量边界。如何维持绝对边界：质量边界不代替验证结果。与后续 L2-L6 的关系：供状态层和验证子系统引用。"""
    @abstractmethod
    def describe_quality_boundary(self, request: QualityBoundaryRequest, trace: TraceContext) -> PortResult[QualityBoundaryResponse]:
        """声明质量边界协议。"""
        raise NotImplementedError


class CandidateValidationPort(ABC):
    """候选验证端口。中文名称：候选验证端口。端口职责：定义候选进入验证的协议。输入输出边界：输入 CandidateValidationRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段候选验证协议。不承担的实现职责：不验证候选、不合入候选。如何服务大模型执行力：使候选从反思进入验证链。如何维持绝对边界：候选验证协议不修改系统。与后续 L2-L6 的关系：供学习、迭代、进化候选使用。"""
    @abstractmethod
    def request_candidate_validation(self, request: CandidateValidationRequest, trace: TraceContext) -> PortResult[CandidateValidationResponse]:
        """声明候选验证协议。"""
        raise NotImplementedError


class LearningTestPort(ABC):
    """学习测试端口。中文名称：学习测试端口。端口职责：定义学习成果测试协议。输入输出边界：输入 LearningTestRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段学习验证协议。不承担的实现职责：不执行学习测试、不写知识库。如何服务大模型执行力：让学习结果可进入测试链。如何维持绝对边界：测试协议不合入学习成果。与后续 L2-L6 的关系：供学习子系统和验证链引用。"""
    @abstractmethod
    def request_learning_test(self, request: LearningTestRequest, trace: TraceContext) -> PortResult[LearningTestResponse]:
        """声明学习测试协议。"""
        raise NotImplementedError


class IterationVerificationPort(ABC):
    """迭代复核端口。中文名称：迭代复核端口。端口职责：定义迭代候选复核协议。输入输出边界：输入 IterationVerificationRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段迭代验证协议。不承担的实现职责：不生成补丁、不合入代码。如何服务大模型执行力：让模型迭代建议可被复核。如何维持绝对边界：复核不等于合入。与后续 L2-L6 的关系：供自我迭代链使用。"""
    @abstractmethod
    def request_iteration_verification(self, request: IterationVerificationRequest, trace: TraceContext) -> PortResult[IterationVerificationResponse]:
        """声明迭代复核协议。"""
        raise NotImplementedError


class EvolutionValidationPort(ABC):
    """进化验证端口。中文名称：进化验证端口。端口职责：定义进化候选验证协议。输入输出边界：输入 EvolutionValidationRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段进化验证协议。不承担的实现职责：不执行进化、不修改架构。如何服务大模型执行力：让长期结构建议具备验证入口。如何维持绝对边界：进化验证不改变系统。与后续 L2-L6 的关系：供自我进化链使用。"""
    @abstractmethod
    def request_evolution_validation(self, request: EvolutionValidationRequest, trace: TraceContext) -> PortResult[EvolutionValidationResponse]:
        """声明进化验证协议。"""
        raise NotImplementedError


class RollbackVerificationPort(ABC):
    """回退验证端口。中文名称：回退验证端口。端口职责：定义回退结果验证协议。输入输出边界：输入 RollbackVerificationRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段回退验证协议。不承担的实现职责：不执行回退、不恢复文件。如何服务大模型执行力：让高影响候选具备可逆性验证入口。如何维持绝对边界：回退验证不触发回退。与后续 L2-L6 的关系：供恢复与版本治理引用。"""
    @abstractmethod
    def request_rollback_verification(self, request: RollbackVerificationRequest, trace: TraceContext) -> PortResult[RollbackVerificationResponse]:
        """声明回退验证协议。"""
        raise NotImplementedError


class RestoreVerificationPort(ABC):
    """恢复验证端口。中文名称：恢复验证端口。端口职责：定义恢复点结果验证协议。输入输出边界：输入 RestoreVerificationRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段恢复验证协议。不承担的实现职责：不执行恢复、不创建恢复点。如何服务大模型执行力：让恢复链有可观察验证入口。如何维持绝对边界：恢复验证不改变状态。与后续 L2-L6 的关系：供状态连续性和恢复子系统引用。"""
    @abstractmethod
    def request_restore_verification(self, request: RestoreVerificationRequest, trace: TraceContext) -> PortResult[RestoreVerificationResponse]:
        """声明恢复验证协议。"""
        raise NotImplementedError


class CandidatePromotionHintPort(ABC):
    """候选晋升提示端口。中文名称：候选晋升提示端口。端口职责：定义候选晋升提示协议。输入输出边界：输入 CandidatePromotionHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段候选治理协议。不承担的实现职责：不真实晋升、不合入候选。如何服务大模型执行力：让候选经过验证后获得下一步提示。如何维持绝对边界：提示不等于执行。与后续 L2-L6 的关系：供候选生命周期与发布链引用。"""
    @abstractmethod
    def submit_candidate_promotion_hint(self, request: CandidatePromotionHintRequest, trace: TraceContext) -> PortResult[CandidatePromotionHintResponse]:
        """声明候选晋升提示协议。"""
        raise NotImplementedError
