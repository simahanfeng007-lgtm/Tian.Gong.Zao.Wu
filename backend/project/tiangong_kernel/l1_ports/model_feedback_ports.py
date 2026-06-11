"""L1 模型反馈端口协议。

本模块在 L1 中的职责：定义模型失败反馈、修正提示、学习意图、工具需求反馈和 Skill 缺口反馈协议。
本模块定义哪些端口：ModelFailureFeedbackPort、ModelCorrectionHintPort、ModelLearningIntentPort、ModelToolNeedFeedbackPort、ModelSkillGapFeedbackPort。
本模块不实现哪些能力：不自动重试，不修改 Skill，不生产工具，不写知识库，不执行真实学习、真实迭代或真实进化。
本模块禁止事项：不得访问文件、网络、数据库、真实工具系统、真实模型系统、插件系统或知识库。
本模块与 L2-L6 的关系：L2 可记录反馈状态，L3 可编排反馈进入候选流程，L4 可实现外部反馈适配，L5 可隔离插件反馈，L6 可由子系统提交反馈。
本模块如何服务“大模型直接控制智能体”：让大模型在失败、卡点、工具不足或 Skill 不足时能直接表达结构化反馈，而不是被沉默阻断。
本模块如何为自我学习、自我迭代、自我进化提供反馈入口：反馈只作为证据和候选入口，后续阶段必须另行验证、裁决和合入。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.content import ContentRef, PayloadRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.goal import GoalRef
from tiangong_kernel.l0_primitives.message import MessageRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.plan import PlanRef
from tiangong_kernel.l0_primitives.relation import RelationRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import PortBoundaryContext, QueryEnvelope
from .port_result import PortResult
from .skill_evolution_ports import SkillCorrectionHint
from .tool_gap_ports import SkillGapReport, ToolNeedReport


@dataclass(frozen=True, slots=True)
class ModelFailureFeedback:
    """模型失败反馈对象。

    作用：表达模型认为任务失败、卡点、下一步建议或边界误解的结构化事实。
    边界：不自动重试，不修改系统，不替代真实验收。
    """

    feedback_ref: ResourceRef
    message_ref: MessageRef | None = None
    skill_ref: SkillRef | None = None
    tool_ref: ToolRef | None = None
    goal_ref: GoalRef | None = None
    plan_ref: PlanRef | None = None
    failure_signal_ref: SignalRef | None = None
    related_observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelCorrectionHint:
    """模型修正提示对象。

    作用：表达模型认为 Skill、工具说明、边界说明或流程说明需要修正的提示。
    边界：不修正 Skill，不修改文件，不写代码，不合入变更。
    """

    hint_ref: ResourceRef
    skill_ref: SkillRef | None = None
    tool_ref: ToolRef | None = None
    relation_ref: RelationRef | None = None
    existing_hint: SkillCorrectionHint | None = None
    content_refs: tuple[ContentRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelLearningIntent:
    """模型学习意图对象。

    作用：表达模型认为系统需要学习某个主题、流程、边界或工具使用方法的意图。
    边界：不执行学习，不读取外部资料，不写知识库，不生成 Skill。
    """

    intent_ref: ResourceRef
    goal_ref: GoalRef | None = None
    skill_ref: SkillRef | None = None
    topic_content_ref: ContentRef | None = None
    payload_ref: PayloadRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelToolNeedFeedback:
    """模型工具需求反馈对象。

    作用：表达模型认为当前 Skill 需要新工具、工具说明不足或工具组不完整。
    边界：不生产工具，不修改工具组，不注册工具。
    """

    feedback_ref: ResourceRef
    skill_ref: SkillRef | None = None
    tool_ref: ToolRef | None = None
    tool_group_ref: ResourceRef | None = None
    action_intent: ActionIntent | None = None
    tool_need_report: ToolNeedReport | None = None
    related_observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelSkillGapFeedback:
    """模型 Skill 缺口反馈对象。

    作用：表达模型认为没有合适 Skill、Skill 说明不足或 Skill 与工具组关系不清。
    边界：不生成 Skill，不修复 Skill，不创建真实版本。
    """

    feedback_ref: ResourceRef
    skill_ref: SkillRef | None = None
    goal_ref: GoalRef | None = None
    plan_ref: PlanRef | None = None
    skill_gap_report: SkillGapReport | None = None
    related_observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelFailureFeedbackRequest:
    """模型失败反馈请求。作用：提交失败反馈事实；边界：不自动重试。"""

    feedback: ModelFailureFeedback
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelFailureFeedbackResponse:
    """模型失败反馈响应。作用：返回失败反馈和审计引用；边界：不代表系统已修改。"""

    feedback: ModelFailureFeedback
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelCorrectionHintRequest:
    """模型修正提示请求。作用：提交修正提示；边界：不修改 Skill 或工具说明。"""

    hint: ModelCorrectionHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelCorrectionHintResponse:
    """模型修正提示响应。作用：返回修正提示和验证引用；边界：不生成补丁。"""

    hint: ModelCorrectionHint
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelLearningIntentRequest:
    """模型学习意图请求。作用：提交学习意图；边界：不执行学习流程。"""

    intent: ModelLearningIntent
    scope_ref: ScopeRef | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelLearningIntentResponse:
    """模型学习意图响应。作用：返回学习意图和证据引用；边界：不生成 Skill。"""

    intent: ModelLearningIntent
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelToolNeedFeedbackRequest:
    """模型工具需求反馈请求。作用：提交工具不足或新工具需求反馈；边界：不生产工具。"""

    feedback: ModelToolNeedFeedback
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelToolNeedFeedbackResponse:
    """模型工具需求反馈响应。作用：返回工具需求反馈和审计引用；边界：不修改工具组。"""

    feedback: ModelToolNeedFeedback
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelSkillGapFeedbackRequest:
    """模型 Skill 缺口反馈请求。作用：提交 Skill 缺口反馈；边界：不生成 Skill。"""

    feedback: ModelSkillGapFeedback
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelSkillGapFeedbackResponse:
    """模型 Skill 缺口反馈响应。作用：返回 Skill 缺口反馈和验证引用；边界：不创建真实版本。"""

    feedback: ModelSkillGapFeedback
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class ModelFailureFeedbackPort(ABC):
    """模型失败反馈端口。

    中文名称：模型失败反馈端口。
    端口职责：定义模型对失败原因、卡点和下一步建议的反馈协议。
    输入输出边界：输入 ModelFailureFeedbackRequest 与 TraceContext，输出 PortResult 包装的 ModelFailureFeedbackResponse。
    所属 L1 层：模型反馈端口协议。
    不承担的实现职责：不自动重试，不修改系统，不替代验收。
    如何服务大模型执行力：让模型遇到边界或工具卡点时能留下可处理反馈。
    如何维持绝对边界：反馈只作为事实引用，不绕过控制面或执行面。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：可作为失败归因和候选改进证据。
    """

    @abstractmethod
    def submit_model_failure_feedback(
        self, request: ModelFailureFeedbackRequest, trace: TraceContext
    ) -> PortResult[ModelFailureFeedbackResponse]:
        """声明模型失败反馈协议。"""
        raise NotImplementedError


class ModelCorrectionHintPort(ABC):
    """模型修正提示端口。

    中文名称：模型修正提示端口。
    端口职责：定义模型对 Skill、工具说明、边界说明或流程说明的修正提示协议。
    输入输出边界：输入 ModelCorrectionHintRequest 与 TraceContext，输出 PortResult 包装的 ModelCorrectionHintResponse。
    所属 L1 层：模型反馈端口协议。
    不承担的实现职责：不改文件，不改 Skill，不生成补丁。
    如何服务大模型执行力：让模型能指出协议或说明不清导致的执行阻滞。
    如何维持绝对边界：修正提示必须等待后续验证和合入流程。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：可进入后续迭代候选池。
    """

    @abstractmethod
    def submit_model_correction_hint(
        self, request: ModelCorrectionHintRequest, trace: TraceContext
    ) -> PortResult[ModelCorrectionHintResponse]:
        """声明模型修正提示协议。"""
        raise NotImplementedError


class ModelLearningIntentPort(ABC):
    """模型学习意图端口。

    中文名称：模型学习意图端口。
    端口职责：定义模型提出系统需要学习什么的意图协议。
    输入输出边界：输入 ModelLearningIntentRequest 与 TraceContext，输出 PortResult 包装的 ModelLearningIntentResponse。
    所属 L1 层：模型反馈端口协议。
    不承担的实现职责：不执行学习，不读取资料，不写知识库，不生成 Skill。
    如何服务大模型执行力：让模型可表达知识或方法缺口，减少重复卡顿。
    如何维持绝对边界：学习意图只是候选输入，不产生真实学习动作。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：是第七阶段正式学习端口的证据入口之一。
    """

    @abstractmethod
    def submit_model_learning_intent(
        self, request: ModelLearningIntentRequest, trace: TraceContext
    ) -> PortResult[ModelLearningIntentResponse]:
        """声明模型学习意图协议。"""
        raise NotImplementedError


class ModelToolNeedFeedbackPort(ABC):
    """模型工具需求反馈端口。

    中文名称：模型工具需求反馈端口。
    端口职责：定义模型反馈工具不足或工具组不完整的协议。
    输入输出边界：输入 ModelToolNeedFeedbackRequest 与 TraceContext，输出 PortResult 包装的 ModelToolNeedFeedbackResponse。
    所属 L1 层：模型反馈端口协议。
    不承担的实现职责：不生产工具，不注册工具，不修改工具组。
    如何服务大模型执行力：让模型能明确说明执行卡点来自工具缺口。
    如何维持绝对边界：工具需求反馈不会直接释放或生成工具。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：可触发后续缺口候选分析但不直接执行。
    """

    @abstractmethod
    def submit_model_tool_need_feedback(
        self, request: ModelToolNeedFeedbackRequest, trace: TraceContext
    ) -> PortResult[ModelToolNeedFeedbackResponse]:
        """声明模型工具需求反馈协议。"""
        raise NotImplementedError


class ModelSkillGapFeedbackPort(ABC):
    """模型 Skill 缺口反馈端口。

    中文名称：模型 Skill 缺口反馈端口。
    端口职责：定义模型反馈 Skill 缺口、说明不足或边界不清的协议。
    输入输出边界：输入 ModelSkillGapFeedbackRequest 与 TraceContext，输出 PortResult 包装的 ModelSkillGapFeedbackResponse。
    所属 L1 层：模型反馈端口协议。
    不承担的实现职责：不生成 Skill，不修复 Skill，不创建版本。
    如何服务大模型执行力：让模型发现没有合适 Skill 时能产生结构化反馈。
    如何维持绝对边界：缺口反馈只是证据，不绕过第七阶段正式流程。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：可作为 Skill 学习和演化候选依据。
    """

    @abstractmethod
    def submit_model_skill_gap_feedback(
        self, request: ModelSkillGapFeedbackRequest, trace: TraceContext
    ) -> PortResult[ModelSkillGapFeedbackResponse]:
        """声明模型 Skill 缺口反馈协议。"""
        raise NotImplementedError
