import pytest

from l4_phase6_builders import phase6_ref, resource_usage
from tiangong_kernel.l4_action_grounding import ExecutionResourceUsage


def test_l4_phase6_resource_usage_is_summary_only():
    usage = resource_usage()

    assert usage.tokens_hint_ref is not None
    assert usage.time_ms_hint_ref is not None
    assert usage.bytes_hint_ref is not None
    assert usage.process_hint_ref is not None
    assert usage.network_hint_ref is not None
    assert usage.allocates_resource is False
    assert usage.makes_resource_policy is False
    assert usage.starts_process is False


def test_l4_phase6_resource_usage_rejects_allocation_or_policy():
    with pytest.raises(ValueError):
        ExecutionResourceUsage(resource_usage_ref=phase6_ref(120, "resource_usage"), allocates_resource=True)
    with pytest.raises(ValueError):
        ExecutionResourceUsage(resource_usage_ref=phase6_ref(121, "resource_usage"), makes_resource_policy=True)
