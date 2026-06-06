"""L1 Skill 演化提示端口协议。

本模块在 L1 中的职责：定义 Skill 演化提示、迭代提示、版本候选提示和修正提示的协议入口。
本模块定义哪些端口：SkillEvolutionHintPort、SkillIterationHintPort、SkillVersionHintPort、SkillCorrectionHintPort。
本模块不实现哪些能力：不执行真实学习、不修改 Skill、不生成新版本、不合入代码、不触发自我迭代或自我进化。
本模块禁止事项：不得访问文件、网络、数据库、插件目录、真实模型系统、真实工具系统或真实知识库。
本模块与 L2-L6 的关系：L2 可记录提示状态，L3 可编排候选证据流，L4 可实现外部适配，L5 可做插件隔离，L6 可由子系统提交提示。
本模块如何服务“大模型先看 Skill，再释放工具组”：只把 Skill 使用后的修正、版本和演化意向表达为证据入口，不改变 Skill 直显主链，不提前执行学习或修改。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.goal import GoalRef
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
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import CommandEnvelope, PortBoundaryContext, QueryEnvelope
from .port_boundary import BoundaryViolation
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class SkillEvolutionHint:
    """Skill 演化提示对象。

    作用：表达某个 Skill 在后续阶段可能需要演化的引用、原因、证据和边界上下文。
    边界：只作为候选提示，不执行演化，不修改架构，不写入任何真实系统。
    """

    skill_ref: SkillRef
    reason_ref: SignalRef | None = None
    goal_ref: GoalRef | None = None
    plan_ref: PlanRef | None = None
    risk_view: RiskView | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillIterationHint:
    """Skill 迭代提示对象。

    作用：表达 Skill 说明、流程、输入输出或工具组关系可能需要小步修正的候选提示。
    边界：不生成补丁，不合入修改，不执行真实迭代。
    """

    skill_ref: SkillRef
    target_relation_ref: RelationRef | None = None
    action_intent: ActionIntent | None = None
    affected_tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    affected_tool_group_ref: ResourceRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillVersionHint:
    """Skill 版本提示对象。

    作用：表达 Skill 可能需要形成候选版本的版本引用、结构引用和证据引用。
    边界：不创建版本，不迁移数据，不替代正式版本治理。
    """

    skill_ref: SkillRef
    current_version_ref: VersionRef | None = None
    candidate_version_ref: VersionRef | None = None
    schema_ref: SchemaRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillCorrectionHint:
    """Skill 修正提示对象。

    作用：表达 Skill 描述、流程、边界或工具组说明可能需要修正的候选意见。
    边界：不改文件，不改注册表，不调用模型，不生成真实修正。
    """

    skill_ref: SkillRef
    correction_signal_ref: SignalRef | None = None
    target_relation_ref: RelationRef | None = None
    command: CommandEnvelope | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillEvolutionHintRequest:
    """Skill 演化提示请求。作用：提交 Skill 可能需要演化的候选提示；边界：不执行演化。"""

    hint: SkillEvolutionHint
    scope_ref: ScopeRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillEvolutionHintResponse:
    """Skill 演化提示响应。作用：返回提示引用、验证引用和越界事实；边界：不代表真实采纳。"""

    hint: SkillEvolutionHint
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillIterationHintRequest:
    """Skill 迭代提示请求。作用：提交 Skill 小步修正候选；边界：不生成补丁。"""

    hint: SkillIterationHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillIterationHintResponse:
    """Skill 迭代提示响应。作用：返回迭代候选提示和证据引用；边界：不合入修改。"""

    hint: SkillIterationHint
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillVersionHintRequest:
    """Skill 版本提示请求。作用：提交 Skill 候选版本提示；边界：不创建真实版本。"""

    hint: SkillVersionHint
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillVersionHintResponse:
    """Skill 版本提示响应。作用：返回候选版本提示和验证引用；边界：不迁移、不发布。"""

    hint: SkillVersionHint
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillCorrectionHintRequest:
    """Skill 修正提示请求。作用：提交 Skill 修正候选意见；边界：不执行修正。"""

    hint: SkillCorrectionHint
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillCorrectionHintResponse:
    """Skill 修正提示响应。作用：返回修正提示和审计引用；边界：不写入真实系统。"""

    hint: SkillCorrectionHint
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class SkillEvolutionHintPort(ABC):
    """Skill 演化提示端口。

    中文名称：Skill 演化提示端口。
    端口职责：定义 Skill 演化候选提示的提交协议。
    输入输出边界：输入 SkillEvolutionHintRequest 与 TraceContext，输出 PortResult 包装的 SkillEvolutionHintResponse。
    所属 L1 层：Skill 直显与工具组端口协议的补丁扩展。
    不承担的实现职责：不执行学习，不执行进化，不修改 Skill 或架构。
    如何服务大模型执行力：让模型使用 Skill 后能表达改进方向，供后续层作为证据。
    如何维持绝对边界：提示不会直接产生真实修改，只保留引用和边界上下文。
    """

    @abstractmethod
    def submit_skill_evolution_hint(
        self, request: SkillEvolutionHintRequest, trace: TraceContext
    ) -> PortResult[SkillEvolutionHintResponse]:
        """声明 Skill 演化提示协议。"""
        raise NotImplementedError


class SkillIterationHintPort(ABC):
    """Skill 迭代提示端口。

    中文名称：Skill 迭代提示端口。
    端口职责：定义 Skill 小步修正候选提示协议。
    输入输出边界：输入 SkillIterationHintRequest 与 TraceContext，输出 PortResult 包装的 SkillIterationHintResponse。
    所属 L1 层：Skill 直显与工具组端口协议的补丁扩展。
    不承担的实现职责：不生成补丁，不合入代码，不改注册表。
    如何服务大模型执行力：让模型能指出 Skill 流程或工具组关系的改进点。
    如何维持绝对边界：只表达候选意图，后续阶段必须另行验证。
    """

    @abstractmethod
    def submit_skill_iteration_hint(
        self, request: SkillIterationHintRequest, trace: TraceContext
    ) -> PortResult[SkillIterationHintResponse]:
        """声明 Skill 迭代提示协议。"""
        raise NotImplementedError


class SkillVersionHintPort(ABC):
    """Skill 版本提示端口。

    中文名称：Skill 版本提示端口。
    端口职责：定义 Skill 候选版本提示协议。
    输入输出边界：输入 SkillVersionHintRequest 与 TraceContext，输出 PortResult 包装的 SkillVersionHintResponse。
    所属 L1 层：Skill 直显与工具组端口协议的补丁扩展。
    不承担的实现职责：不创建版本，不迁移数据，不发布版本。
    如何服务大模型执行力：为后续 Skill 版本演进保留证据入口。
    如何维持绝对边界：版本提示不是版本事实，不能绕过验证和边界层。
    """

    @abstractmethod
    def submit_skill_version_hint(
        self, request: SkillVersionHintRequest, trace: TraceContext
    ) -> PortResult[SkillVersionHintResponse]:
        """声明 Skill 版本提示协议。"""
        raise NotImplementedError


class SkillCorrectionHintPort(ABC):
    """Skill 修正提示端口。

    中文名称：Skill 修正提示端口。
    端口职责：定义 Skill 描述、流程、边界或工具组说明的修正提示协议。
    输入输出边界：输入 SkillCorrectionHintRequest 与 TraceContext，输出 PortResult 包装的 SkillCorrectionHintResponse。
    所属 L1 层：Skill 直显与工具组端口协议的补丁扩展。
    不承担的实现职责：不改文件，不写注册表，不调用模型。
    如何服务大模型执行力：让模型反馈 Skill 说明中阻碍执行的结构问题。
    如何维持绝对边界：修正提示只进入证据链，不直接改变系统。
    """

    @abstractmethod
    def submit_skill_correction_hint(
        self, request: SkillCorrectionHintRequest, trace: TraceContext
    ) -> PortResult[SkillCorrectionHintResponse]:
        """声明 Skill 修正提示协议。"""
        raise NotImplementedError
