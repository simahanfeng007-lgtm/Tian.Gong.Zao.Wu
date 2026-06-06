"""L1 学习端口协议。

本模块在 L1 中的职责：定义学习意图、学习任务候选、学习证据、学习结果引用、学习边界和学习反馈协议。
本模块定义哪些端口：LearningIntentPort、LearningTaskPort、LearningEvidencePort、LearningResultPort、LearningBoundaryPort、LearningFeedbackPort。
本模块不实现哪些能力：不执行学习、不读取资料、不写知识库、不生成 Skill、不生产工具、不训练模型。
本模块禁止事项：不得访问文件、网络、数据库、模型、工具、插件或真实知识库。
本模块与 L2-L6 的关系：L2 可记录学习状态，L3 可编排候选，L4 可实现外部学习适配，L5 可隔离插件，L6 可提交子系统学习意图。
本模块如何服务工程生命体：把失败、反思、缺口和用户要求转成可复核的学习候选。
本模块如何保证学习 / 迭代 / 进化不绕过边界：学习只形成候选、证据和反馈，不能直接改系统。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.goal import GoalRef
from tiangong_kernel.l0_primitives.learning import ExperienceRef, LearningRef, LessonRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef

from .envelope import PortBoundaryContext, QueryEnvelope
from .model_feedback_ports import ModelFailureFeedback, ModelLearningIntent, ModelSkillGapFeedback, ModelToolNeedFeedback
from .model_reflection_ports import ModelOutcomeAssessment, ModelReflection
from .port_boundary import PortBoundary
from .port_result import PortResult
from .tool_gap_ports import SkillGapReport, ToolGroupGapReport, ToolNeedReport


@dataclass(frozen=True, slots=True)
class LearningIntent:
    """学习意图对象。

    作用：表达模型反思、任务失败、Skill 缺口、工具缺口或用户要求形成的学习意图。
    边界：不执行学习，不读取资料，不写知识库，不生成 Skill。
    """

    intent_ref: ResourceRef
    learning_ref: LearningRef
    model_learning_intent: ModelLearningIntent | None = None
    failure_feedback: ModelFailureFeedback | None = None
    skill_gap_feedback: ModelSkillGapFeedback | None = None
    skill_gap_report: SkillGapReport | None = None
    tool_need_feedback: ModelToolNeedFeedback | None = None
    tool_need_report: ToolNeedReport | None = None
    goal_ref: GoalRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningCandidate:
    """学习候选对象。

    作用：表达可进入后续验证流程的学习任务候选。
    边界：不读取资料，不生成知识，不生成 Skill。
    """

    candidate_ref: ResourceRef
    learning_ref: LearningRef | None = None
    intent: LearningIntent | None = None
    experience_ref: ExperienceRef | None = None
    lesson_ref: LessonRef | None = None
    skill_ref: SkillRef | None = None
    skill_gap_report: SkillGapReport | None = None
    tool_need_report: ToolNeedReport | None = None
    tool_group_gap_report: ToolGroupGapReport | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningEvidence:
    """学习证据对象。

    作用：表达学习候选与观察、模型反思、结果评估和证据之间的引用关系。
    边界：不抓取网页，不读取文件，不写证据库。
    """

    evidence_ref: EvidenceRef
    learning_ref: LearningRef | None = None
    model_reflection: ModelReflection | None = None
    outcome_assessment: ModelOutcomeAssessment | None = None
    observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningResult:
    """学习结果引用对象。

    作用：表达学习结果的引用、教训引用和验证引用。
    边界：不写知识库，不合入 Skill，不生产工具。
    """

    learning_ref: LearningRef
    result_ref: ResourceRef | None = None
    lesson_ref: LessonRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


LearningResultReference = LearningResult


@dataclass(frozen=True, slots=True)
class LearningBoundary:
    """学习边界对象。

    作用：表达学习候选的范围、策略和停止或降级边界。
    边界：不执行真实裁决，不批准学习，不阻断大模型行动。
    """

    learning_ref: LearningRef
    boundary: PortBoundary | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningFeedback:
    """学习反馈对象。

    作用：表达学习候选质量、缺口和后续建议的反馈引用。
    边界：不更新模型，不更新 Skill，不写知识库。
    """

    feedback_ref: SignalRef
    learning_ref: LearningRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningIntentRequest:
    """学习意图请求。作用：提交学习意图；边界：不执行学习。"""

    intent: LearningIntent
    scope_ref: ScopeRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningIntentResponse:
    """学习意图响应。作用：返回学习意图；边界：不生成 Skill。"""

    intent: LearningIntent
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningTaskRequest:
    """学习任务请求。作用：提交学习候选；边界：不读取资料。"""

    candidate: LearningCandidate
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningTaskResponse:
    """学习任务响应。作用：返回学习候选；边界：不写知识库。"""

    candidate: LearningCandidate
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningEvidenceRequest:
    """学习证据请求。作用：提交学习证据引用；边界：不生成证据。"""

    evidence: LearningEvidence
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningEvidenceResponse:
    """学习证据响应。作用：返回学习证据引用；边界：不写证据库。"""

    evidence: LearningEvidence
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningResultRequest:
    """学习结果请求。作用：提交学习结果引用；边界：不合入。"""

    result: LearningResult
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningResultResponse:
    """学习结果响应。作用：返回学习结果引用；边界：不生产工具。"""

    result: LearningResult
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningBoundaryRequest:
    """学习边界请求。作用：提交学习边界；边界：不裁决。"""

    boundary: LearningBoundary
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningBoundaryResponse:
    """学习边界响应。作用：返回学习边界；边界：不批准学习。"""

    boundary: LearningBoundary
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningFeedbackRequest:
    """学习反馈请求。作用：提交学习反馈；边界：不更新模型。"""

    feedback: LearningFeedback
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LearningFeedbackResponse:
    """学习反馈响应。作用：返回学习反馈；边界：不更新 Skill。"""

    feedback: LearningFeedback
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class LearningIntentPort(ABC):
    """学习意图端口。

    中文名称：学习意图端口。
    端口职责：定义学习意图提交协议。
    输入输出边界：输入 LearningIntentRequest 与 TraceContext，输出 PortResult 包装的 LearningIntentResponse。
    所属 L1 层：学习协议入口。
    不承担的实现职责：不执行学习，不读取资料，不写知识库。
    如何服务大模型执行力：把模型反思和缺口转成可复核候选。
    如何维持绝对边界：学习意图不能直接改系统。
    与后续 L2-L6 的关系：后续层可实现状态、编排、适配和子系统学习。
    """

    @abstractmethod
    def submit_learning_intent(self, request: LearningIntentRequest, trace: TraceContext) -> PortResult[LearningIntentResponse]:
        """声明学习意图协议。"""
        raise NotImplementedError


class LearningTaskPort(ABC):
    """学习任务端口。

    中文名称：学习任务端口。
    端口职责：定义学习候选任务协议。
    输入输出边界：输入 LearningTaskRequest 与 TraceContext，输出 PortResult 包装的 LearningTaskResponse。
    所属 L1 层：学习协议入口。
    不承担的实现职责：不读取资料，不生成知识，不生成 Skill。
    如何服务大模型执行力：让学习需求成为明确任务候选。
    如何维持绝对边界：候选任务必须等待验证和边界处理。
    与后续 L2-L6 的关系：L3 可编排，L4 可实现，L6 可提交候选。
    """

    @abstractmethod
    def submit_learning_task(self, request: LearningTaskRequest, trace: TraceContext) -> PortResult[LearningTaskResponse]:
        """声明学习任务候选协议。"""
        raise NotImplementedError


class LearningEvidencePort(ABC):
    """学习证据端口。

    中文名称：学习证据端口。
    端口职责：定义学习证据引用协议。
    输入输出边界：输入 LearningEvidenceRequest 与 TraceContext，输出 PortResult 包装的 LearningEvidenceResponse。
    所属 L1 层：学习协议入口。
    不承担的实现职责：不抓取网页，不读取文件，不写证据库。
    如何服务大模型执行力：让学习候选具备可追溯依据。
    如何维持绝对边界：证据只作为引用，不释放内容。
    与后续 L2-L6 的关系：第八阶段可验证证据完整性。
    """

    @abstractmethod
    def attach_learning_evidence(self, request: LearningEvidenceRequest, trace: TraceContext) -> PortResult[LearningEvidenceResponse]:
        """声明学习证据协议。"""
        raise NotImplementedError


class LearningResultPort(ABC):
    """学习结果端口。

    中文名称：学习结果端口。
    端口职责：定义学习结果引用协议。
    输入输出边界：输入 LearningResultRequest 与 TraceContext，输出 PortResult 包装的 LearningResultResponse。
    所属 L1 层：学习协议入口。
    不承担的实现职责：不写知识库，不合入 Skill，不生产工具。
    如何服务大模型执行力：让学习结果能被后续层作为候选引用。
    如何维持绝对边界：结果引用不是正式合入。
    与后续 L2-L6 的关系：后续层可实现验证、适配和子系统沉淀。
    """

    @abstractmethod
    def declare_learning_result(self, request: LearningResultRequest, trace: TraceContext) -> PortResult[LearningResultResponse]:
        """声明学习结果协议。"""
        raise NotImplementedError


class LearningBoundaryPort(ABC):
    """学习边界端口。

    中文名称：学习边界端口。
    端口职责：定义学习范围、停止和降级边界协议。
    输入输出边界：输入 LearningBoundaryRequest 与 TraceContext，输出 PortResult 包装的 LearningBoundaryResponse。
    所属 L1 层：学习协议入口。
    不承担的实现职责：不执行裁决，不批准学习，不阻断大模型行动。
    如何服务大模型执行力：用边界说明支持安全连续学习。
    如何维持绝对边界：边界协议必须先于真实学习适配。
    与后续 L2-L6 的关系：后续层可实现策略和复核流程。
    """

    @abstractmethod
    def describe_learning_boundary(self, request: LearningBoundaryRequest, trace: TraceContext) -> PortResult[LearningBoundaryResponse]:
        """声明学习边界协议。"""
        raise NotImplementedError


class LearningFeedbackPort(ABC):
    """学习反馈端口。

    中文名称：学习反馈端口。
    端口职责：定义学习候选质量反馈协议。
    输入输出边界：输入 LearningFeedbackRequest 与 TraceContext，输出 PortResult 包装的 LearningFeedbackResponse。
    所属 L1 层：学习协议入口。
    不承担的实现职责：不更新模型，不更新 Skill，不写知识库。
    如何服务大模型执行力：让学习过程中的问题可回流为候选。
    如何维持绝对边界：反馈不会直接改变系统。
    与后续 L2-L6 的关系：后续层可实现复核和适配。
    """

    @abstractmethod
    def submit_learning_feedback(self, request: LearningFeedbackRequest, trace: TraceContext) -> PortResult[LearningFeedbackResponse]:
        """声明学习反馈协议。"""
        raise NotImplementedError
