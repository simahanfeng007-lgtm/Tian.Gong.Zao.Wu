"""L0 成本、预算、配额与频率限制事实语言原语。

本模块在 L0 中的职责：定义成本、预算、配额、频率限制和成本估计/实际值的引用事实。
本模块只表达：成本类型、金额、预算窗口、配额窗口、频率窗口和状态事实。
本模块明确不做：计费、扣费、限流、模型路由、预算优化或 token 实际计算。
禁止事项：不得阻断请求，不得执行价格绑定，不得计算真实调用成本。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class CostKind(str, Enum):
    """成本类别：只表达成本来源类型；UNKNOWN 表示类别未知。

    MONEY：金额；TOKEN：token；COMPUTE：计算；TIME：时间；STORAGE：存储；NETWORK：网络；CONTEXT：上下文；
    TOOL_CALL：工具调用；ENERGY：能量；OPPORTUNITY：机会成本；UNKNOWN：未知兜底。
    """
    MONEY="money"; TOKEN="token"; COMPUTE="compute"; TIME="time"; STORAGE="storage"; NETWORK="network"; CONTEXT="context"; TOOL_CALL="tool_call"; ENERGY="energy"; OPPORTUNITY="opportunity"; UNKNOWN="unknown"
class BudgetKind(str, Enum):
    """预算类别：只表达预算边界所属对象；UNKNOWN 表示类别未知。"""
    RUN_BUDGET="run_budget"; SESSION_BUDGET="session_budget"; GOAL_BUDGET="goal_budget"; PLAN_BUDGET="plan_budget"; ACTOR_BUDGET="actor_budget"; PLUGIN_BUDGET="plugin_budget"; RESOURCE_BUDGET="resource_budget"; CONTEXT_BUDGET="context_budget"; MONETARY_BUDGET="monetary_budget"; UNKNOWN="unknown"
class QuotaKind(str, Enum):
    """配额类别：只表达次数、容量或并发类额度；UNKNOWN 表示类别未知。"""
    CALL_COUNT="call_count"; TOKEN_COUNT="token_count"; BYTE_COUNT="byte_count"; TIME_QUOTA="time_quota"; STORAGE_QUOTA="storage_quota"; CONCURRENCY="concurrency"; EFFECT_COUNT="effect_count"; TRANSACTION_COUNT="transaction_count"; UNKNOWN="unknown"
class RateLimitKind(str, Enum):
    """频率限制类别：只表达单位窗口内频率边界；UNKNOWN 表示类别未知。"""
    REQUESTS_PER_SECOND="requests_per_second"; CALLS_PER_MINUTE="calls_per_minute"; TOKENS_PER_MINUTE="tokens_per_minute"; EFFECTS_PER_WINDOW="effects_per_window"; BYTES_PER_WINDOW="bytes_per_window"; CONCURRENCY_LIMIT="concurrency_limit"; UNKNOWN="unknown"
class BudgetState(str, Enum):
    """预算状态：只表达预算可用性状态；UNKNOWN 表示状态未知。"""
    AVAILABLE="available"; NEAR_LIMIT="near_limit"; EXHAUSTED="exhausted"; THROTTLED="throttled"; SUSPENDED="suspended"; RESET="reset"; OVERRIDDEN="overridden"; UNKNOWN="unknown"
class QuotaState(str, Enum):
    """配额状态：只表达配额可用性状态；UNKNOWN 表示状态未知。"""
    AVAILABLE="available"; NEAR_LIMIT="near_limit"; EXHAUSTED="exhausted"; THROTTLED="throttled"; SUSPENDED="suspended"; RESET="reset"; OVERRIDDEN="overridden"; UNKNOWN="unknown"
class RateLimitState(str, Enum):
    """频率限制状态：只表达频率边界可用性状态；UNKNOWN 表示状态未知。"""
    AVAILABLE="available"; NEAR_LIMIT="near_limit"; EXHAUSTED="exhausted"; THROTTLED="throttled"; SUSPENDED="suspended"; RESET="reset"; OVERRIDDEN="overridden"; UNKNOWN="unknown"

@dataclass(frozen=True, slots=True)
class CostAmount:
    """成本金额。

    作用：表达成本数量和值对象。
    所属 L0 边界：只保存 amount、unit 与 kind，不绑定价格表。
    不能承担的上层职责：不能计费、扣费或计算真实 token。
    字段：amount 为成本数值；unit 为单位。
    """
    amount: float = 0.0; unit: str = "unit"; kind: CostKind = CostKind.UNKNOWN; schema_version: str = "0.1"
    def __post_init__(self)->None:
        if not self.unit: raise ValueError("CostAmount.unit cannot be empty")
        if not self.schema_version: raise ValueError("CostAmount.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class BudgetWindow:
    """预算窗口。作用：表达预算有效窗口引用；所属 L0 边界：只保存 window_id 与时间引用；不能承担调度职责。"""
    value: RefId; start_ref: TypedRef|None=None; end_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("BudgetWindow.schema_version cannot be empty")
QuotaWindow = BudgetWindow
RateLimitWindow = BudgetWindow
@dataclass(frozen=True, slots=True)
class CostRef:
    """成本引用。作用：表达行动、副作用、资源使用或事务的成本引用；所属 L0 边界：只保存 cost_id、kind 和 amount；不能承担计费职责。"""
    value: RefId; kind: CostKind=CostKind.UNKNOWN; amount: CostAmount|None=None; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("CostRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class BudgetRef:
    """预算引用。作用：表达 Actor、Run、Goal、Plan、Session、Scope 或 Plugin 的预算边界；所属 L0 边界：只保存 budget_id、kind、state 和 window；不能优化预算。"""
    value: RefId; kind: BudgetKind=BudgetKind.UNKNOWN; state: BudgetState=BudgetState.UNKNOWN; window: BudgetWindow|None=None; owner_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("BudgetRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class QuotaRef:
    """配额引用。作用：表达次数、容量、额度或配额引用；所属 L0 边界：只保存 quota_id、kind、state 和 window；不能扣减配额。"""
    value: RefId; kind: QuotaKind=QuotaKind.UNKNOWN; state: QuotaState=QuotaState.UNKNOWN; window: QuotaWindow|None=None; owner_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("QuotaRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class RateLimitRef:
    """频率限制引用。作用：表达单位时间内允许发生的调用、请求或资源消耗边界；所属 L0 边界：只保存 rate_limit_id、kind、state 和 window；不能执行限流。"""
    value: RefId; kind: RateLimitKind=RateLimitKind.UNKNOWN; state: RateLimitState=RateLimitState.UNKNOWN; window: RateLimitWindow|None=None; owner_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("RateLimitRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class CostEstimateRef:
    """成本预估引用。作用：表达执行前预估成本；所属 L0 边界：只保存 estimate_id 与 cost_ref；不能路由模型或阻断请求。"""
    value: RefId; cost_ref: CostRef|None=None; confidence_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("CostEstimateRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class CostActualRef:
    """实际成本引用。作用：表达执行后实际成本引用；所属 L0 边界：只保存 actual_id 与 cost_ref；不能扣费或回写账单。"""
    value: RefId; cost_ref: CostRef|None=None; evidence_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("CostActualRef.schema_version cannot be empty")
