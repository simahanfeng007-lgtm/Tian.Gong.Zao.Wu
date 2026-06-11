"""L0 学习、适应与演化事实语言原语。

本模块在 L0 中的职责：定义学习引用、适应引用、演化引用、改进候选、评估、提交、回退、经历和教训引用。
本模块只表达：系统从观察、事件、失败、反馈、记忆或人工干预中获得可复用信息的事实引用。
本模块明确不做：模型训练、代码修改、工具生成、自动合并、长期结构变更执行、偏好学习计算。
禁止事项：不得生成真实工具，不得修改代码，不得调用模型，不得执行自我演化流程。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class LearningKind(str, Enum):
    """学习类型枚举：只标记学习事实来源和沉淀方向；UNKNOWN 表示未知或暂不分类。

    EPISODIC_LEARNING：情节学习；SEMANTIC_LEARNING：语义学习；PROCEDURAL_LEARNING：程序性学习；FAILURE_LEARNING：失败学习；
    FEEDBACK_LEARNING：反馈学习；PREFERENCE_LEARNING：偏好学习；POLICY_LEARNING：策略学习引用；UNKNOWN：未知兜底。
    """

    EPISODIC_LEARNING = "episodic_learning"
    SEMANTIC_LEARNING = "semantic_learning"
    PROCEDURAL_LEARNING = "procedural_learning"
    FAILURE_LEARNING = "failure_learning"
    FEEDBACK_LEARNING = "feedback_learning"
    PREFERENCE_LEARNING = "preference_learning"
    POLICY_LEARNING = "policy_learning"
    UNKNOWN = "unknown"


class LearningState(str, Enum):
    """学习状态枚举：表达学习事实所处阶段；UNKNOWN 表示状态未知。

    PROPOSED：已提出；ASSESSING：评估中；APPROVED：已批准；ACTIVE：活动中；COMMITTED：已提交事实；
    REJECTED：已拒绝；ROLLED_BACK：已回退事实；QUARANTINED：已隔离；ARCHIVED：已归档；UNKNOWN：未知兜底。
    """

    PROPOSED = "proposed"
    ASSESSING = "assessing"
    APPROVED = "approved"
    ACTIVE = "active"
    COMMITTED = "committed"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"
    QUARANTINED = "quarantined"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class AdaptationKind(str, Enum):
    """适应类型枚举：只表达临时调整的事实类别；UNKNOWN 表示未知或暂不分类。

    CONTEXT_ADAPTATION：上下文适应；PLAN_ADAPTATION：计划适应；POLICY_ADAPTATION：策略适应引用；RESOURCE_ADAPTATION：资源适应；
    MEMORY_ADAPTATION：记忆适应；RETRIEVAL_ADAPTATION：检索适应引用；CONTROL_MODE_ADAPTATION：控制模式适应；UNKNOWN：未知兜底。
    """

    CONTEXT_ADAPTATION = "context_adaptation"
    PLAN_ADAPTATION = "plan_adaptation"
    POLICY_ADAPTATION = "policy_adaptation"
    RESOURCE_ADAPTATION = "resource_adaptation"
    MEMORY_ADAPTATION = "memory_adaptation"
    RETRIEVAL_ADAPTATION = "retrieval_adaptation"
    CONTROL_MODE_ADAPTATION = "control_mode_adaptation"
    UNKNOWN = "unknown"


class AdaptationState(str, Enum):
    """适应状态枚举：表达临时调整事实阶段；UNKNOWN 表示状态未知。

    PROPOSED：已提出；ASSESSING：评估中；APPROVED：已批准；ACTIVE：活动中；COMMITTED：已提交事实；
    REJECTED：已拒绝；ROLLED_BACK：已回退事实；QUARANTINED：已隔离；ARCHIVED：已归档；UNKNOWN：未知兜底。
    """

    PROPOSED = "proposed"
    ASSESSING = "assessing"
    APPROVED = "approved"
    ACTIVE = "active"
    COMMITTED = "committed"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"
    QUARANTINED = "quarantined"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class EvolutionKind(str, Enum):
    """演化类型枚举：只表达长期结构改变的事实类别；UNKNOWN 表示未知或暂不分类。

    MEMORY_EVOLUTION：记忆演化；SKILL_EVOLUTION：技能演化引用；TOOL_EVOLUTION：工具演化引用；PLUGIN_EVOLUTION：插件演化引用；
    POLICY_EVOLUTION：策略演化；CONTRACT_EVOLUTION：契约演化；SCHEMA_EVOLUTION：结构版本演化；CODE_EVOLUTION：代码演化引用；
    ARCHITECTURE_EVOLUTION：架构演化；UNKNOWN：未知兜底。
    """

    MEMORY_EVOLUTION = "memory_evolution"
    SKILL_EVOLUTION = "skill_evolution"
    TOOL_EVOLUTION = "tool_evolution"
    PLUGIN_EVOLUTION = "plugin_evolution"
    POLICY_EVOLUTION = "policy_evolution"
    CONTRACT_EVOLUTION = "contract_evolution"
    SCHEMA_EVOLUTION = "schema_evolution"
    CODE_EVOLUTION = "code_evolution"
    ARCHITECTURE_EVOLUTION = "architecture_evolution"
    UNKNOWN = "unknown"


class EvolutionState(str, Enum):
    """演化状态枚举：表达长期结构改变事实阶段；UNKNOWN 表示状态未知。

    PROPOSED：已提出；ASSESSING：评估中；APPROVED：已批准；ACTIVE：活动中；COMMITTED：已提交事实；
    REJECTED：已拒绝；ROLLED_BACK：已回退事实；QUARANTINED：已隔离；ARCHIVED：已归档；UNKNOWN：未知兜底。
    """

    PROPOSED = "proposed"
    ASSESSING = "assessing"
    APPROVED = "approved"
    ACTIVE = "active"
    COMMITTED = "committed"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"
    QUARANTINED = "quarantined"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ExperienceRef:
    """经历引用。

    作用：表达可被学习沉淀的经历事实引用。
    所属 L0 边界：只保存 experience_id、origin_ref 和 evidence_refs。
    不能承担的上层职责：不能抽取经验，不能生成规则，不能写入长期结构。
    字段：value 为经历引用 ID；origin_ref 为来源引用。
    """

    value: RefId
    origin_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ExperienceRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LessonRef:
    """教训引用。

    作用：表达从失败、反馈或人工干预中沉淀的可复用教训引用。
    所属 L0 边界：只保存 lesson_id、experience_ref 和 evidence_refs。
    不能承担的上层职责：不能自动改策略，不能触发修复，不能生成技能。
    字段：value 为教训引用 ID；experience_ref 为经历引用。
    """

    value: RefId
    experience_ref: ExperienceRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("LessonRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ImprovementProposalRef:
    """改进候选引用。

    作用：表达候选改进事项的引用事实。
    所属 L0 边界：只保存 proposal_id、subject_ref 和 evidence_refs。
    不能承担的上层职责：不能生成补丁，不能合并更新，不能执行改进。
    字段：value 为候选引用 ID；subject_ref 为被改进对象引用。
    """

    value: RefId
    subject_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ImprovementProposalRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ImprovementAssessmentRef:
    """改进评估引用。

    作用：表达候选改进的评估事实引用。
    所属 L0 边界：只保存 assessment_id、proposal_ref、decision_ref 和 evidence_refs。
    不能承担的上层职责：不能计算评分，不能批准执行，不能改写候选。
    字段：value 为评估引用 ID；proposal_ref 为候选改进引用。
    """

    value: RefId
    proposal_ref: ImprovementProposalRef | None = None
    decision_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ImprovementAssessmentRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionCommitRef:
    """演化提交引用。

    作用：表达某项演化已经被提交的事实引用。
    所属 L0 边界：只保存 commit_id、evolution_ref 和 evidence_refs。
    不能承担的上层职责：不能执行提交，不能修改文件、代码或外部系统。
    字段：value 为提交引用 ID；evolution_ref 为演化引用。
    """

    value: RefId
    evolution_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("EvolutionCommitRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionRollbackRef:
    """演化回退引用。

    作用：表达某项演化被回退的事实引用。
    所属 L0 边界：只保存 rollback_id、evolution_ref、reason_ref 和 evidence_refs。
    不能承担的上层职责：不能执行回退，不能恢复文件、代码或外部系统。
    字段：value 为回退引用 ID；reason_ref 为回退原因引用。
    """

    value: RefId
    evolution_ref: TypedRef | None = None
    reason_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("EvolutionRollbackRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LearningRef:
    """学习引用。

    作用：表达系统从观察、事件、经历、失败、反馈、记忆或人工干预中获得可复用信息的事实引用。
    所属 L0 边界：只保存 learning_id、kind、state、experience_ref、lesson_ref 和证据引用。
    不能承担的上层职责：不能训练模型，不能生成技能，不能更新偏好算法。
    字段：value 为学习引用 ID；kind 为学习类型；state 为学习状态。
    """

    value: RefId
    kind: LearningKind = LearningKind.UNKNOWN
    state: LearningState = LearningState.UNKNOWN
    experience_ref: ExperienceRef | None = None
    lesson_ref: LessonRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("LearningRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AdaptationRef:
    """适应引用。

    作用：表达系统在不永久改变核心结构时，对当前策略、上下文、资源、行为或计划进行调整的事实引用。
    所属 L0 边界：只保存 adaptation_id、kind、state、subject_ref 和证据引用。
    不能承担的上层职责：不能执行调整，不能修改计划或策略。
    字段：value 为适应引用 ID；subject_ref 为被适应对象引用。
    """

    value: RefId
    kind: AdaptationKind = AdaptationKind.UNKNOWN
    state: AdaptationState = AdaptationState.UNKNOWN
    subject_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("AdaptationRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionRef:
    """演化引用。

    作用：表达系统对长期结构、能力、策略、记忆、工具、插件、技能、代码或合约进行版本化改变的事实引用。
    所属 L0 边界：只保存 evolution_id、kind、state、proposal_ref、assessment_ref、commit_ref、rollback_ref。
    不能承担的上层职责：不能修改代码，不能生成工具，不能合并更新，不能执行自我演化。
    字段：value 为演化引用 ID；kind 为演化类型；state 为演化状态。
    """

    value: RefId
    kind: EvolutionKind = EvolutionKind.UNKNOWN
    state: EvolutionState = EvolutionState.UNKNOWN
    proposal_ref: ImprovementProposalRef | None = None
    assessment_ref: ImprovementAssessmentRef | None = None
    commit_ref: EvolutionCommitRef | None = None
    rollback_ref: EvolutionRollbackRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("EvolutionRef.schema_version cannot be empty")
