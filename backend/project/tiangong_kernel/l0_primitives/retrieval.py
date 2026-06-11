"""L0 索引、查询与检索引用事实语言原语。

本模块在 L0 中的职责：定义索引、查询、检索、结果、证据、排序依据和过滤条件引用。
本模块只表达：检索相关事实引用与状态，不取回真实内容。
本模块明确不做：索引构建、搜索、排序、数据库查询或外部搜索。
禁止事项：不得执行检索算法，不得访问向量库或全文库，不得连接外部搜索源。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef

class IndexKind(str, Enum):
    """索引类别：表达索引所代表的组织方式；UNKNOWN 表示索引类别未知。"""
    FULL_TEXT="full_text"; VECTOR="vector"; GRAPH="graph"; TEMPORAL="temporal"; SEMANTIC="semantic"; TAG="tag"; RELATION="relation"; EVENT="event"; MEMORY="memory"; ARTIFACT="artifact"; HYBRID="hybrid"; UNKNOWN="unknown"
class IndexState(str, Enum):
    """索引状态：表达索引生命周期；UNKNOWN 表示状态未知。"""
    PROPOSED="proposed"; BUILDING="building"; ACTIVE="active"; STALE="stale"; DEGRADED="degraded"; DISABLED="disabled"; DEPRECATED="deprecated"; ARCHIVED="archived"; UNKNOWN="unknown"
class QueryKind(str, Enum):
    """查询类别：表达查询意图形态；UNKNOWN 表示查询类别未知。"""
    KEYWORD="keyword"; SEMANTIC="semantic"; TEMPORAL="temporal"; GRAPH="graph"; RELATIONAL="relational"; HYBRID="hybrid"; FILTERED="filtered"; DIAGNOSTIC="diagnostic"; UNKNOWN="unknown"
class RetrievalKind(str, Enum):
    """检索类别：表达检索对象来源；UNKNOWN 表示检索类别未知。"""
    MEMORY_RETRIEVAL="memory_retrieval"; EVENT_RETRIEVAL="event_retrieval"; EVIDENCE_RETRIEVAL="evidence_retrieval"; ARTIFACT_RETRIEVAL="artifact_retrieval"; CONTEXT_RETRIEVAL="context_retrieval"; GRAPH_RETRIEVAL="graph_retrieval"; EXTERNAL_RETRIEVAL="external_retrieval"; HYBRID_RETRIEVAL="hybrid_retrieval"; UNKNOWN="unknown"
class RetrievalState(str, Enum):
    """检索状态：表达检索事实生命周期；UNKNOWN 表示状态未知。"""
    PROPOSED="proposed"; AUTHORIZED="authorized"; RUNNING="running"; SUCCEEDED="succeeded"; EMPTY="empty"; PARTIAL="partial"; FAILED="failed"; BLOCKED="blocked"; EXPIRED="expired"; ARCHIVED="archived"; UNKNOWN="unknown"
@dataclass(frozen=True, slots=True)
class IndexRef:
    """索引引用。作用：表达对象、记忆、事件、证据、产物、关系、上下文、指标或内容的索引引用；所属 L0 边界：只保存 index_id、kind 与 state；不能构建索引。字段：value 为 index_id。"""
    value: RefId; kind: IndexKind=IndexKind.UNKNOWN; state: IndexState=IndexState.UNKNOWN; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("IndexRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class QueryIntentRef:
    """查询意图引用。作用：表达查询意图的引用事实；所属 L0 边界：只保存 intent_id 与 goal_ref；不能生成查询。字段：value 为 intent_id。"""
    value: RefId; goal_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("QueryIntentRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class QueryScopeRef:
    """查询作用域引用。作用：表达查询适用范围引用；所属 L0 边界：只保存 query_scope_id 与 scope_ref；不能筛选真实数据。字段：value 为查询作用域引用 ID。"""
    value: RefId; scope_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("QueryScopeRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class QueryRef:
    """查询引用。作用：表达 Actor、Run、Goal、Plan 或 Context 发起的查询事实；所属 L0 边界：只保存 query_id、kind、intent_ref 与 scope_ref；不能执行查询。字段：kind 为查询类别。"""
    value: RefId; kind: QueryKind=QueryKind.UNKNOWN; intent_ref: QueryIntentRef|None=None; scope_ref: QueryScopeRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("QueryRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class RetrievalResultRef:
    """检索结果引用。作用：表达检索结果集合引用；所属 L0 边界：只保存 result_id 与 result_digest_ref；不能保存完整结果列表。字段：value 为 result_id。"""
    value: RefId; result_digest_ref: TypedRef|None=None; count: int=0; schema_version: str="0.1"
    def __post_init__(self)->None:
        if self.count < 0: raise ValueError("RetrievalResultRef.count cannot be negative")
        if not self.schema_version: raise ValueError("RetrievalResultRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class RetrievalEvidenceRef:
    """检索证据引用。作用：表达检索过程或结果的证据引用；所属 L0 边界：只保存 retrieval_evidence_id 与 evidence_ref；不能验证证据。字段：value 为检索证据引用 ID。"""
    value: RefId; evidence_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("RetrievalEvidenceRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class RankingRef:
    """排序依据引用。作用：表达检索结果排序依据引用；所属 L0 边界：只保存 ranking_id 与 policy_ref；不能排序结果。字段：value 为排序依据引用 ID。"""
    value: RefId; policy_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("RankingRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class FilterRef:
    """过滤条件引用。作用：表达检索时使用的过滤条件引用；所属 L0 边界：只保存 filter_id 与 scope_ref；不能过滤真实数据。字段：value 为过滤条件引用 ID。"""
    value: RefId; scope_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("FilterRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class RetrievalRef:
    """检索引用。作用：表达从索引、存储、记忆、图、事件流或外部源中取回相关信息的事实引用；所属 L0 边界：只保存 retrieval_id、kind、state 与引用；不能取回真实信息。字段：value 为 retrieval_id。"""
    value: RefId; kind: RetrievalKind=RetrievalKind.UNKNOWN; state: RetrievalState=RetrievalState.UNKNOWN; index_ref: IndexRef|None=None; query_ref: QueryRef|None=None; result_ref: RetrievalResultRef|None=None; ranking_ref: RankingRef|None=None; filter_ref: FilterRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("RetrievalRef.schema_version cannot be empty")
