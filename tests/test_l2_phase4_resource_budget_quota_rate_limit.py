from tiangong_kernel.l2_state import ResourceKind, ResourceStatus
from tests.test_l2_phase4_serialization import build_phase4_objects


def test_l2_phase4_resource_budget_records_external_snapshots():
    budget = build_phase4_objects()["budget"]

    assert budget.resource_status is ResourceStatus.LIMITED
    assert budget.resource_kind is ResourceKind.TOKEN_BUDGET
    assert budget.limit_snapshot == "limit:1000"
    assert budget.used_snapshot == "used:200"
    assert budget.remaining_snapshot == "remaining:800"


def test_l2_phase4_quota_and_rate_limit_record_refs_without_waiting_or_retrying():
    objects = build_phase4_objects()
    quota = objects["quota"]
    rate_limit = objects["rate_limit"]

    assert quota.resource_kind is ResourceKind.TOOL_CALL_BUDGET
    assert quota.window_ref is not None
    assert rate_limit.resource_status is ResourceStatus.RATE_LIMITED
    assert rate_limit.retry_after_ref is not None
    assert rate_limit.applies_to_refs
    assert not hasattr(rate_limit, "sleep")
    assert not hasattr(rate_limit, "retry")


def test_l2_phase4_resource_lease_and_pressure_are_record_only():
    objects = build_phase4_objects()
    lease = objects["lease"]
    pressure = objects["pressure"]

    assert lease.resource_kind is ResourceKind.TOOL_LEASE
    assert lease.tool_group_release_state_ref == objects["phase3"]["tool_release"].identity.state_ref
    assert lease.granted_scope_refs
    assert pressure.resource_state_refs
    assert pressure.suggested_boundary_refs == (objects["boundary_check"].identity.state_ref,)
    assert not hasattr(lease, "renew")
    assert not hasattr(pressure, "degrade")
