"""L0 关系、依赖与图引用事实语言原语。

本模块在 L0 中的职责：定义事实对象之间的语义关系、依赖、图、节点、边和路径引用。
本模块只表达：关系引用、依赖引用、图结构引用和关系强度事实。
本模块明确不做：图计算、依赖解析、排序、关系推理或知识图谱实现。
禁止事项：不得访问图存储，不得执行图算法，不得进行向量检索。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef

class RelationKind(str, Enum):
    """关系类别：表达两个或多个事实对象间的语义关系；UNKNOWN 表示关系未知。"""
    USES="uses"; GENERATES="generates"; DERIVES_FROM="derives_from"; SUPPORTS="supports"; CONTRADICTS="contradicts"; REPLACES="replaces"; REFERENCES="references"; ASSOCIATED_WITH="associated_with"; CAUSES="causes"; PART_OF="part_of"; OWNED_BY="owned_by"; BOUND_TO="bound_to"; GOVERNS="governs"; VALIDATES="validates"; INVALIDATES="invalidates"; UNKNOWN="unknown"
class RelationDirection(str, Enum):
    """关系方向：表达关系方向性；UNKNOWN 表示方向未知。"""
    DIRECTED="directed"; REVERSE="reverse"; BIDIRECTIONAL="bidirectional"; UNDIRECTED="undirected"; UNKNOWN="unknown"
class RelationState(str, Enum):
    """关系状态：表达关系生命周期；UNKNOWN 表示状态未知。"""
    PROPOSED="proposed"; ACTIVE="active"; WEAKENED="weakened"; CONFLICTED="conflicted"; DEPRECATED="deprecated"; REVOKED="revoked"; ARCHIVED="archived"; UNKNOWN="unknown"
class DependencyKind(str, Enum):
    """依赖类别：表达运行、结构、证据、资源、策略或生命周期依赖类型；UNKNOWN 表示依赖未知。"""
    RUNTIME="runtime"; RESOURCE="resource"; POLICY="policy"; CONTRACT="contract"; EVIDENCE="evidence"; ARTIFACT="artifact"; LIFECYCLE="lifecycle"; SCHEMA="schema"; TRUST="trust"; UNKNOWN="unknown"
class DependencyState(str, Enum):
    """依赖状态：表达依赖生命周期；UNKNOWN 表示状态未知。"""
    PROPOSED="proposed"; ACTIVE="active"; WEAKENED="weakened"; CONFLICTED="conflicted"; DEPRECATED="deprecated"; REVOKED="revoked"; ARCHIVED="archived"; UNKNOWN="unknown"
@dataclass(frozen=True, slots=True)
class RelationStrength:
    """关系强度。作用：表达关系强弱数值事实；所属 L0 边界：只保存 value 与 evidence_refs；不能推理关系。字段：value 为强度值。"""
    value: float=0.0; evidence_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("RelationStrength.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class RelationRef:
    """关系引用。作用：表达两个或多个 L0/L2 事实对象之间的语义关系引用；所属 L0 边界：只保存 relation_id、kind、source_ref、target_ref；不能进行关系推理。字段：value 为 relation_id。"""
    value: RefId; kind: RelationKind=RelationKind.UNKNOWN; direction: RelationDirection=RelationDirection.UNKNOWN; state: RelationState=RelationState.UNKNOWN; source_ref: TypedRef|None=None; target_ref: TypedRef|None=None; strength: RelationStrength|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("RelationRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class DependencyRef:
    """依赖引用。作用：表达一个对象对另一个对象的运行、结构、证据、资源、策略或生命周期依赖；所属 L0 边界：只保存 dependency_id 与引用关系；不能解析依赖。字段：kind 为依赖类别。"""
    value: RefId; kind: DependencyKind=DependencyKind.UNKNOWN; state: DependencyState=DependencyState.UNKNOWN; source_ref: TypedRef|None=None; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("DependencyRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class GraphRef:
    """图引用。作用：表达一组节点、边和路径构成的关系图引用；所属 L0 边界：只保存 graph_id 与图摘要引用；不能遍历图。字段：value 为 graph_id。"""
    value: RefId; digest_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("GraphRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class NodeRef:
    """节点引用。作用：表达图中节点的引用事实；所属 L0 边界：只保存 node_id 与 target_ref；不能装载节点内容。字段：value 为 node_id。"""
    value: RefId; target_ref: TypedRef|None=None; graph_ref: GraphRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("NodeRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class EdgeRef:
    """边引用。作用：表达图中边的引用事实；所属 L0 边界：只保存 edge_id 与 relation_ref；不能计算路径。字段：value 为 edge_id。"""
    value: RefId; relation_ref: RelationRef|None=None; graph_ref: GraphRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("EdgeRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class PathRef:
    """路径引用。作用：表达图中路径的引用事实；所属 L0 边界：只保存 path_id 与 edge_refs；不能寻找路径。字段：edge_refs 为边引用集合。"""
    value: RefId; edge_refs: tuple[EdgeRef,...]=field(default_factory=tuple); graph_ref: GraphRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("PathRef.schema_version cannot be empty")
