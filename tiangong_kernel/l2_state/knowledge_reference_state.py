"""L2 知识引用状态对象，只记录知识来源、hash、摘要、可见性、新旧和可信事实，不实现知识系统。

作用：为学习材料、上下文和检索结果保留知识引用层面的稳定状态事实。
边界：不抽取知识，不写入知识库，不生成 SkillSeed、SkillVersion、SkillPatch 或 Tool 需求。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class KnowledgeReferenceKind(str, Enum):
    """知识引用类型枚举。

    作用：表达知识引用来自规则、方法、事实、接口说明、设计说明、代码说明或外部材料。
    边界：不实现知识分类器，不抽取知识，不生成 Skill。
    """

    UNKNOWN = "unknown"
    RULE = "rule"
    METHOD = "method"
    FACT = "fact"
    INTERFACE_NOTE = "interface_note"
    DESIGN_NOTE = "design_note"
    CODE_NOTE = "code_note"
    EXTERNAL_MATERIAL = "external_material"


class KnowledgeReferenceVisibility(str, Enum):
    """知识引用可见性枚举。

    作用：表达知识引用是否隐藏、引用可见、模型可见、人类可见、受限、过期或撤销。
    边界：不执行可见性过滤，不暴露知识正文。
    """

    UNKNOWN = "unknown"
    HIDDEN = "hidden"
    REF_VISIBLE = "ref_visible"
    MODEL_VISIBLE = "model_visible"
    HUMAN_VISIBLE = "human_visible"
    LIMITED = "limited"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class KnowledgeReferenceState:
    """知识引用状态对象。

    作用：记录知识引用、来源、类型、内容 hash、摘要、可见性、新鲜度、可信度和边界事实。
    边界：不抽取知识，不写知识库，不生成 Skill 或 Tool 需求。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    knowledge_ref_id: TypedRef | None = None
    source_ref: TypedRef | None = None
    knowledge_kind: KnowledgeReferenceKind = KnowledgeReferenceKind.UNKNOWN
    content_hash: str = ""
    summary: str = ""
    visibility: KnowledgeReferenceVisibility = KnowledgeReferenceVisibility.UNKNOWN
    freshness: str = "unknown"
    trust_level: str = "unknown"
    boundary_status: L2StateBoundary | None = None
    related_learning_ref: TypedRef | None = None
    related_retrieval_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("KnowledgeReferenceState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("KnowledgeReferenceState.schema_version cannot be empty")
