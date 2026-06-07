"""L1 自我进化端口协议。

本模块在 L1 中的职责：定义进化意图、进化候选、进化边界、进化证据、进化决策提示、进化回滚提示和连续性协议。
本模块定义哪些端口：EvolutionIntentPort、EvolutionCandidatePort、EvolutionBoundaryPort、EvolutionEvidencePort、EvolutionDecisionHintPort、EvolutionRollbackHintPort、EvolutionContinuityPort。
本模块不实现哪些能力：不执行真实进化、不修改架构、不生成插件、不生成工具、不改代码、不合入候选、不执行回滚。
本模块禁止事项：不得访问文件、数据库、网络、真实代码系统、真实模型系统、真实工具系统或插件系统。
本模块与 L2-L6 的关系：L2 可记录进化状态，L3 可编排候选流，L4 可实现外部适配，L5 可隔离插件进化边界，L6 可提交子系统进化候选。
本模块如何服务工程生命体：让长期失败、Skill 长期不足、工具组长期缺失和模型反思进入可验证的进化候选链。
本模块如何保证学习 / 迭代 / 进化不绕过边界：进化只提交意图、候选、证据、提示和连续性声明，不直接改变工程结构。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.decision import Decision
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.learning import EvolutionRef, ImprovementProposalRef
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
from .learning_ports import LearningResult
from .model_reflection_ports import ModelEvolutionHint, ModelIterationHint, ModelReflection
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult
from .self_iteration_ports import IterationCandidate, IterationRollbackHint
from .skill_evolution_ports import SkillEvolutionHint
from .tool_gap_ports import SkillGapReport, ToolGroupGapReport, ToolNeedReport


@dataclass(frozen=True, slots=True)
class EvolutionIntent:
    """进化意图对象。

    作用：表达系统可能需要长期结构调整的意图来源和证据。
    边界：不执行进化，不修改架构，不生成候选变更。
    """

    intent_ref: ResourceRef
    evolution_ref: EvolutionRef
    model_evolution_hint: ModelEvolutionHint | None = None
    skill_evolution_hint: SkillEvolutionHint | None = None
    skill_gap_report: SkillGapReport | None = None
    tool_need_report: ToolNeedReport | None = None
    learning_result: LearningResult | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionCandidate:
    """进化候选对象。

    作用：表达可被后续验证和复核的结构级进化候选。
    边界：不修改架构，不生成插件，不生成工具，不改代码。
    """

    candidate_ref: ResourceRef
    evolution_ref: EvolutionRef | None = None
    proposal_ref: ImprovementProposalRef | None = None
    iteration_candidate: IterationCandidate | None = None
    intent: EvolutionIntent | None = None
    skill_ref: SkillRef | None = None
    tool_ref: ToolRef | None = None
    relation_ref: RelationRef | None = None
    model_reflection: ModelReflection | None = None
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionBoundary:
    """进化边界对象。

    作用：表达进化候选的建议范围、必须验证范围、确认范围和禁止范围。
    边界：不执行真实裁决，不放行候选，不提升权限。
    """

    candidate_ref: ResourceRef | None = None
    boundary: PortBoundary | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    risk_view: RiskView | None = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionEvidence:
    """进化证据对象。

    作用：表达进化候选依据的验证、测试、学习结果和模型反思引用。
    边界：不生成证据，不写审计库，不执行测试。
    """

    candidate_ref: ResourceRef | None = None
    learning_result: LearningResult | None = None
    model_iteration_hint: ModelIterationHint | None = None
    skill_evolution_hint: SkillEvolutionHint | None = None
    tool_group_gap_report: ToolGroupGapReport | None = None
    tool_need_report: ToolNeedReport | None = None
    test_refs: tuple[TestRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionDecisionHint:
    """进化决策提示对象。

    作用：表达进化候选可能需要接受、拒绝、降级或转交验证的提示。
    边界：不做真实决策，不合入候选，不触发执行。
    """

    candidate_ref: ResourceRef | None = None
    decision: Decision | None = None
    risk_view: RiskView | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionRollbackHint:
    """进化回滚提示对象。

    作用：表达进化候选若失败可能需要回退、隔离或降级的提示。
    边界：不执行回滚，不恢复文件，不修改版本。
    """

    hint_ref: ResourceRef
    candidate_ref: ResourceRef | None = None
    evolution_ref: EvolutionRef | None = None
    iteration_rollback_hint: IterationRollbackHint | None = None
    version_ref: VersionRef | None = None
    audit_ref: AuditRef | None = None
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionContinuity:
    """进化连续性对象。

    作用：表达进化前后必须保持的 Skill 可理解性、工具组可释放性、边界不被绕过和 L0/L1 边界不污染。
    边界：不执行进化迁移，不修改结构，不验证真实连续性。
    """

    continuity_ref: ResourceRef
    candidate_ref: ResourceRef | None = None
    skill_refs: tuple[SkillRef, ...] = field(default_factory=tuple)
    tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    relation_refs: tuple[RelationRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionIntentRequest:
    """进化意图请求。作用：提交进化意图；边界：不执行进化。"""

    intent: EvolutionIntent
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionIntentResponse:
    """进化意图响应。作用：返回进化意图和证据引用；边界：不修改架构。"""

    intent: EvolutionIntent
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionCandidateRequest:
    """进化候选请求。作用：提交进化候选；边界：不生成插件或工具。"""

    candidate: EvolutionCandidate
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionCandidateResponse:
    """进化候选响应。作用：返回进化候选和验证引用；边界：不改代码。"""

    candidate: EvolutionCandidate
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionBoundaryRequest:
    """进化边界请求。作用：声明进化边界；边界：不放行执行。"""

    boundary: EvolutionBoundary
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionBoundaryResponse:
    """进化边界响应。作用：返回进化边界和越界事实；边界：不做真实裁决。"""

    boundary: EvolutionBoundary
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionEvidenceRequest:
    """进化证据请求。作用：提交进化证据引用；边界：不生成证据。"""

    evidence: EvolutionEvidence
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionEvidenceResponse:
    """进化证据响应。作用：返回进化证据和审计引用；边界：不写审计库。"""

    evidence: EvolutionEvidence
    audit_ref: AuditRef | None = None
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionDecisionHintRequest:
    """进化决策提示请求。作用：提交决策提示；边界：不做真实决策。"""

    hint: EvolutionDecisionHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionDecisionHintResponse:
    """进化决策提示响应。作用：返回决策提示和验证引用；边界：不合入候选。"""

    hint: EvolutionDecisionHint
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionRollbackHintRequest:
    """进化回滚提示请求。作用：提交回滚提示；边界：不执行回滚。"""

    hint: EvolutionRollbackHint
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionRollbackHintResponse:
    """进化回滚提示响应。作用：返回回滚提示和验证引用；边界：不恢复版本。"""

    hint: EvolutionRollbackHint
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionContinuityRequest:
    """进化连续性请求。作用：声明连续性约束；边界：不执行迁移。"""

    continuity: EvolutionContinuity
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvolutionContinuityResponse:
    """进化连续性响应。作用：返回连续性声明和越界事实；边界：不验证真实迁移。"""

    continuity: EvolutionContinuity
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class EvolutionIntentPort(ABC):
    """进化意图端口。

    中文名称：进化意图端口。
    端口职责：定义长期结构调整意图提交协议。
    输入输出边界：输入 EvolutionIntentRequest 与 TraceContext，输出 PortResult 包装的 EvolutionIntentResponse。
    所属 L1 层：自我进化协议入口。
    不承担的实现职责：不执行进化，不修改架构，不生成候选变更。
    如何服务大模型执行力：让重复失败和长期缺口可进入结构化候选链。
    如何维持绝对边界：进化意图必须等待后续验证和复核。
    与后续 L2-L6 的关系：后续层可接入状态、验证、适配和插件隔离。
    """

    @abstractmethod
    def submit_evolution_intent(
        self, request: EvolutionIntentRequest, trace: TraceContext
    ) -> PortResult[EvolutionIntentResponse]:
        """声明进化意图协议。"""
        raise NotImplementedError


class EvolutionCandidatePort(ABC):
    """进化候选端口。

    中文名称：进化候选端口。
    端口职责：定义进化候选提交协议。
    输入输出边界：输入 EvolutionCandidateRequest 与 TraceContext，输出 PortResult 包装的 EvolutionCandidateResponse。
    所属 L1 层：自我进化协议入口。
    不承担的实现职责：不改架构，不生成插件，不生产工具，不改代码。
    如何服务大模型执行力：让系统可记录候选进化方向而不断链。
    如何维持绝对边界：候选不是执行动作。
    与后续 L2-L6 的关系：后续层可进行验证、复核和合规适配。
    """

    @abstractmethod
    def submit_evolution_candidate(
        self, request: EvolutionCandidateRequest, trace: TraceContext
    ) -> PortResult[EvolutionCandidateResponse]:
        """声明进化候选协议。"""
        raise NotImplementedError


class EvolutionBoundaryPort(ABC):
    """进化边界端口。

    中文名称：进化边界端口。
    端口职责：定义进化候选的边界、策略和风险说明协议。
    输入输出边界：输入 EvolutionBoundaryRequest 与 TraceContext，输出 PortResult 包装的 EvolutionBoundaryResponse。
    所属 L1 层：自我进化协议入口。
    不承担的实现职责：不做真实裁决，不放行候选，不提升权限。
    如何服务大模型执行力：让模型理解进化建议的可行范围。
    如何维持绝对边界：边界说明不是执行许可。
    与后续 L2-L6 的关系：后续层可接入策略、验证和人工确认。
    """

    @abstractmethod
    def describe_evolution_boundary(
        self, request: EvolutionBoundaryRequest, trace: TraceContext
    ) -> PortResult[EvolutionBoundaryResponse]:
        """声明进化边界协议。"""
        raise NotImplementedError


class EvolutionEvidencePort(ABC):
    """进化证据端口。

    中文名称：进化证据端口。
    端口职责：定义进化候选证据引用协议。
    输入输出边界：输入 EvolutionEvidenceRequest 与 TraceContext，输出 PortResult 包装的 EvolutionEvidenceResponse。
    所属 L1 层：自我进化协议入口。
    不承担的实现职责：不生成证据，不写审计库，不执行测试。
    如何服务大模型执行力：让结构级改进有可追踪依据。
    如何维持绝对边界：证据引用不等于验证通过。
    与后续 L2-L6 的关系：后续层可接入验证、审计和候选晋升。
    """

    @abstractmethod
    def attach_evolution_evidence(
        self, request: EvolutionEvidenceRequest, trace: TraceContext
    ) -> PortResult[EvolutionEvidenceResponse]:
        """声明进化证据协议。"""
        raise NotImplementedError


class EvolutionDecisionHintPort(ABC):
    """进化决策提示端口。

    中文名称：进化决策提示端口。
    端口职责：定义进化候选的决策提示协议。
    输入输出边界：输入 EvolutionDecisionHintRequest 与 TraceContext，输出 PortResult 包装的 EvolutionDecisionHintResponse。
    所属 L1 层：自我进化协议入口。
    不承担的实现职责：不做真实决策，不合入候选，不触发执行。
    如何服务大模型执行力：让系统可表达候选下一步处理方向。
    如何维持绝对边界：决策提示必须等待后续正式决策流程。
    与后续 L2-L6 的关系：后续层可接入决策、验证和状态记录。
    """

    @abstractmethod
    def submit_evolution_decision_hint(
        self, request: EvolutionDecisionHintRequest, trace: TraceContext
    ) -> PortResult[EvolutionDecisionHintResponse]:
        """声明进化决策提示协议。"""
        raise NotImplementedError


class EvolutionRollbackHintPort(ABC):
    """进化回滚提示端口。

    中文名称：进化回滚提示端口。
    端口职责：定义进化候选失败时的回退提示协议。
    输入输出边界：输入 EvolutionRollbackHintRequest 与 TraceContext，输出 PortResult 包装的 EvolutionRollbackHintResponse。
    所属 L1 层：自我进化协议入口。
    不承担的实现职责：不执行回滚，不恢复文件，不修改版本。
    如何服务大模型执行力：让结构级改进保留可逆性说明。
    如何维持绝对边界：回退提示必须等待第八阶段验证协议。
    与后续 L2-L6 的关系：后续层可接入版本治理、验证和审计。
    """

    @abstractmethod
    def submit_evolution_rollback_hint(
        self, request: EvolutionRollbackHintRequest, trace: TraceContext
    ) -> PortResult[EvolutionRollbackHintResponse]:
        """声明进化回滚提示协议。"""
        raise NotImplementedError


class EvolutionContinuityPort(ABC):
    """进化连续性端口。

    中文名称：进化连续性端口。
    端口职责：定义进化前后主链连续性和边界不污染协议。
    输入输出边界：输入 EvolutionContinuityRequest 与 TraceContext，输出 PortResult 包装的 EvolutionContinuityResponse。
    所属 L1 层：自我进化协议入口。
    不承担的实现职责：不执行迁移，不验证真实连续性，不修改结构。
    如何服务大模型执行力：保证 Skill、工具组和边界链条在候选层保持清晰。
    如何维持绝对边界：连续性声明不绕过验证和边界处理。
    与后续 L2-L6 的关系：后续层可在验证、迁移和插件隔离中引用。
    """

    @abstractmethod
    def describe_evolution_continuity(
        self, request: EvolutionContinuityRequest, trace: TraceContext
    ) -> PortResult[EvolutionContinuityResponse]:
        """声明进化连续性协议。"""
        raise NotImplementedError
