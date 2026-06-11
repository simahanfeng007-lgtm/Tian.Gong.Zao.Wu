"""L1 模型反思端口协议。

本模块在 L1 中的职责：定义模型任务反思、自评、结果评估、进化提示和迭代提示端口。
本模块定义哪些端口：ModelReflectionPort、ModelSelfReviewPort、ModelOutcomeAssessmentPort、ModelEvolutionHintPort、ModelIterationHintPort。
本模块不实现哪些能力：不执行改进、不保存长期记忆、不做自动评分、不替代测试、不修改架构、不生成补丁、不回滚版本。
本模块禁止事项：不得调用真实模型、不得执行工具、不得写文件、不得加载插件、不得触发真实学习、迭代或进化。
本模块与 L2-L6 的关系：L2 可记录反思状态，L3 可编排反思证据流，L4 可实现外部适配，L5 可限制插件反思范围，L6 可由子系统提交反思与候选提示。
本模块如何服务“大模型直接控制智能体”：让大模型在完成或失败后用结构化反思描述质量、路径、结果和候选改进，不替它执行修改。
本模块如何为自我学习、自我迭代、自我进化提供反馈入口：反思、评估、迭代提示和进化提示只作为第七阶段及以后候选证据，不直接改变系统。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.decision import Decision, DecisionRef
from tiangong_kernel.l0_primitives.effect import EffectRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.failure import FailureRef, RootCauseRef
from tiangong_kernel.l0_primitives.goal import GoalRef
from tiangong_kernel.l0_primitives.metric import MetricRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.plan import PlanRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.relation import RelationRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import TestRef, ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import PortBoundaryContext, QueryEnvelope
from .model_envelope_ports import ModelResponseEnvelope
from .model_feedback_ports import ModelFailureFeedback, ModelSkillGapFeedback, ModelToolNeedFeedback
from .port_boundary import BoundaryViolation
from .port_result import PortResult
from .skill_evolution_ports import SkillEvolutionHint, SkillIterationHint


@dataclass(frozen=True, slots=True)
class ModelReflection:
    """模型反思对象。

    作用：表达模型对一次任务、一次 Skill 使用或一次工具组调用链的反思引用。
    边界：不执行改进，不保存长期记忆，不修改系统。
    """

    goal_ref: GoalRef | None = None
    plan_ref: PlanRef | None = None
    skill_ref: SkillRef | None = None
    tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    response_envelope: ModelResponseEnvelope | None = None
    failure_feedback: ModelFailureFeedback | None = None
    observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelSelfReview:
    """模型自评对象。

    作用：表达模型对自身输出质量、行动路径、错误原因和可验证依据的自评。
    边界：不做自动评分算法，不触发真实改写，不替代外部验证。
    """

    response_envelope: ModelResponseEnvelope | None = None
    root_cause_ref: RootCauseRef | None = None
    decision_ref: DecisionRef | None = None
    metric_refs: tuple[MetricRef, ...] = field(default_factory=tuple)
    test_refs: tuple[TestRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelOutcomeAssessment:
    """模型结果评估对象。

    作用：表达模型对任务结果、效果、失败事实和验证引用的评估。
    边界：不做真实验收，不替代测试，不替代验证端口。
    """

    goal_ref: GoalRef | None = None
    effect_refs: tuple[EffectRef, ...] = field(default_factory=tuple)
    failure_ref: FailureRef | None = None
    decision: Decision | None = None
    observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelEvolutionHint:
    """模型进化提示对象。

    作用：表达模型认为系统可能需要结构级演化的提示、范围、风险和证据引用。
    边界：不执行进化，不修改架构，不生成候选变更。
    """

    skill_ref: SkillRef | None = None
    tool_group_ref: ResourceRef | None = None
    target_relation_ref: RelationRef | None = None
    evolution_signal_ref: SignalRef | None = None
    skill_evolution_hint: SkillEvolutionHint | None = None
    risk_view: RiskView | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelIterationHint:
    """模型迭代提示对象。

    作用：表达模型认为系统可能需要小步迭代、说明修正或工具关系调整的提示。
    边界：不生成补丁，不合入代码，不回滚版本。
    """

    skill_ref: SkillRef | None = None
    tool_ref: ToolRef | None = None
    action_intent: ActionIntent | None = None
    skill_iteration_hint: SkillIterationHint | None = None
    tool_need_feedback: ModelToolNeedFeedback | None = None
    skill_gap_feedback: ModelSkillGapFeedback | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    version_ref: VersionRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelReflectionRequest:
    """模型反思请求。作用：提交模型任务反思；边界：不保存长期记忆。"""

    reflection: ModelReflection
    scope_ref: ScopeRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelReflectionResponse:
    """模型反思响应。作用：返回模型反思和审计引用；边界：不执行改进。"""

    reflection: ModelReflection
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelSelfReviewRequest:
    """模型自评请求。作用：提交模型自评；边界：不做自动评分。"""

    review: ModelSelfReview
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelSelfReviewResponse:
    """模型自评响应。作用：返回模型自评和验证引用；边界：不触发改写。"""

    review: ModelSelfReview
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelOutcomeAssessmentRequest:
    """模型结果评估请求。作用：提交任务结果评估；边界：不替代测试。"""

    assessment: ModelOutcomeAssessment
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelOutcomeAssessmentResponse:
    """模型结果评估响应。作用：返回结果评估和测试引用；边界：不做真实验收。"""

    assessment: ModelOutcomeAssessment
    test_refs: tuple[TestRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelEvolutionHintRequest:
    """模型进化提示请求。作用：提交系统进化提示；边界：不执行进化。"""

    hint: ModelEvolutionHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelEvolutionHintResponse:
    """模型进化提示响应。作用：返回进化提示和越界事实；边界：不修改架构。"""

    hint: ModelEvolutionHint
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelIterationHintRequest:
    """模型迭代提示请求。作用：提交系统小步迭代提示；边界：不生成补丁。"""

    hint: ModelIterationHint
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelIterationHintResponse:
    """模型迭代提示响应。作用：返回迭代提示和版本引用；边界：不合入修改。"""

    hint: ModelIterationHint
    version_ref: VersionRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class ModelReflectionPort(ABC):
    """模型反思端口。

    中文名称：模型反思端口。
    端口职责：定义模型对任务、Skill 使用和工具组调用链的反思协议。
    输入输出边界：输入 ModelReflectionRequest 与 TraceContext，输出 PortResult 包装的 ModelReflectionResponse。
    所属 L1 层：ModelPort、模型会话信封、模型反馈与反思协议。
    不承担的实现职责：不执行改进，不保存长期记忆，不修改系统。
    如何服务大模型执行力：让模型能复盘路径并给出后续可验证线索。
    如何维持绝对边界：反思只作为证据，不产生真实动作。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：是后续候选证据入口。
    """

    @abstractmethod
    def submit_model_reflection(
        self, request: ModelReflectionRequest, trace: TraceContext
    ) -> PortResult[ModelReflectionResponse]:
        """声明模型反思提交协议。"""
        raise NotImplementedError


class ModelSelfReviewPort(ABC):
    """模型自评端口。

    中文名称：模型自评端口。
    端口职责：定义模型对自身输出质量、行动路径和错误原因的自评协议。
    输入输出边界：输入 ModelSelfReviewRequest 与 TraceContext，输出 PortResult 包装的 ModelSelfReviewResponse。
    所属 L1 层：ModelPort、模型会话信封、模型反馈与反思协议。
    不承担的实现职责：不做自动评分算法，不触发真实改写。
    如何服务大模型执行力：让模型可说明自身输出是否足以继续执行。
    如何维持绝对边界：自评不替代测试和验证端口。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：自评可进入后续评估证据链。
    """

    @abstractmethod
    def submit_model_self_review(
        self, request: ModelSelfReviewRequest, trace: TraceContext
    ) -> PortResult[ModelSelfReviewResponse]:
        """声明模型自评提交协议。"""
        raise NotImplementedError


class ModelOutcomeAssessmentPort(ABC):
    """模型结果评估端口。

    中文名称：模型结果评估端口。
    端口职责：定义模型对任务结果和验证证据的评估协议。
    输入输出边界：输入 ModelOutcomeAssessmentRequest 与 TraceContext，输出 PortResult 包装的 ModelOutcomeAssessmentResponse。
    所属 L1 层：ModelPort、模型会话信封、模型反馈与反思协议。
    不承担的实现职责：不做真实验收，不替代测试，不替代验证。
    如何服务大模型执行力：让模型基于结果引用决定后续表达和修正方向。
    如何维持绝对边界：结果评估仍需由测试和验证链确认。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：评估结果可作为后续候选筛选依据。
    """

    @abstractmethod
    def submit_model_outcome_assessment(
        self, request: ModelOutcomeAssessmentRequest, trace: TraceContext
    ) -> PortResult[ModelOutcomeAssessmentResponse]:
        """声明模型结果评估提交协议。"""
        raise NotImplementedError


class ModelEvolutionHintPort(ABC):
    """模型进化提示端口。

    中文名称：模型进化提示端口。
    端口职责：定义模型提出系统可能需要结构级演化的提示协议。
    输入输出边界：输入 ModelEvolutionHintRequest 与 TraceContext，输出 PortResult 包装的 ModelEvolutionHintResponse。
    所属 L1 层：ModelPort、模型会话信封、模型反馈与反思协议。
    不承担的实现职责：不执行进化，不修改架构，不生成候选变更。
    如何服务大模型执行力：让模型能指出系统结构可能阻碍执行的地方。
    如何维持绝对边界：进化提示只进入后续候选治理流程。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：这是第七阶段正式进化端口的预留证据入口。
    """

    @abstractmethod
    def submit_model_evolution_hint(
        self, request: ModelEvolutionHintRequest, trace: TraceContext
    ) -> PortResult[ModelEvolutionHintResponse]:
        """声明模型进化提示提交协议。"""
        raise NotImplementedError


class ModelIterationHintPort(ABC):
    """模型迭代提示端口。

    中文名称：模型迭代提示端口。
    端口职责：定义模型提出系统可能需要小步迭代的提示协议。
    输入输出边界：输入 ModelIterationHintRequest 与 TraceContext，输出 PortResult 包装的 ModelIterationHintResponse。
    所属 L1 层：ModelPort、模型会话信封、模型反馈与反思协议。
    不承担的实现职责：不生成补丁，不合入代码，不回滚版本。
    如何服务大模型执行力：让模型提出可验证的小步改进候选。
    如何维持绝对边界：迭代提示不等于真实修改。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：这是第七阶段正式迭代端口的预留证据入口。
    """

    @abstractmethod
    def submit_model_iteration_hint(
        self, request: ModelIterationHintRequest, trace: TraceContext
    ) -> PortResult[ModelIterationHintResponse]:
        """声明模型迭代提示提交协议。"""
        raise NotImplementedError
