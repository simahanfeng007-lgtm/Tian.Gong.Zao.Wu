from dataclasses import FrozenInstanceError
import pytest
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.serialization import stable_json_dumps, stable_hash

def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "9" * 32)

def assert_frozen(obj):
    with pytest.raises(FrozenInstanceError):
        obj.schema_version = "x"

def assert_stable(obj):
    assert stable_json_dumps(obj) == stable_json_dumps(obj)
    assert stable_hash(obj) == stable_hash(obj)

from tiangong_kernel.l0_primitives.cost_budget import CostKind, CostAmount, CostRef, BudgetKind, BudgetWindow, BudgetRef, BudgetState, QuotaKind, QuotaRef, QuotaState, RateLimitKind, RateLimitRef, RateLimitState, CostEstimateRef, CostActualRef

def test_cost_budget_objects_construct_freeze_serialize_hash_and_enum_values():
    amount = CostAmount(3.0, "token", CostKind.TOKEN)
    cost = CostRef(rid(), CostKind.TOKEN, amount)
    window = BudgetWindow(rid())
    budget = BudgetRef(rid(), BudgetKind.RUN_BUDGET, BudgetState.AVAILABLE, window)
    quota = QuotaRef(rid(), QuotaKind.CALL_COUNT, QuotaState.NEAR_LIMIT, window)
    rate = RateLimitRef(rid(), RateLimitKind.CALLS_PER_MINUTE, RateLimitState.THROTTLED, window)
    estimate = CostEstimateRef(rid(), cost)
    actual = CostActualRef(rid(), cost)
    assert CostKind.OPPORTUNITY.value == "opportunity"
    assert BudgetKind.MONETARY_BUDGET.value == "monetary_budget"
    assert QuotaKind.TRANSACTION_COUNT.value == "transaction_count"
    assert RateLimitKind.CONCURRENCY_LIMIT.value == "concurrency_limit"
    for obj in (amount, cost, window, budget, quota, rate, estimate, actual):
        assert_frozen(obj); assert_stable(obj)
