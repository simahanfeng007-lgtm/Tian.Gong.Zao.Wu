import pytest

from l4_phase5_builders import phase5_ref
from tiangong_kernel.l4_action_grounding import ResourceUsageDescriptor


def test_l4_phase5_resource_usage_descriptor_is_summary_only():
    descriptor = ResourceUsageDescriptor(
        resource_usage_ref=phase5_ref(130, "resource_usage"),
        summary="time tokens bytes cpu network process hints",
        time_hint_ref=phase5_ref(131, "time_hint"),
        token_hint_ref=phase5_ref(132, "token_hint"),
        byte_hint_ref=phase5_ref(133, "byte_hint"),
        cpu_hint_ref=phase5_ref(134, "cpu_hint"),
        network_hint_ref=phase5_ref(135, "network_hint"),
        process_hint_ref=phase5_ref(136, "process_hint"),
        usage_items=(("time", "preview"), ("bytes", "ref_only")),
    )

    assert descriptor.descriptor_only is True
    assert descriptor.allocates_resource is False
    assert descriptor.starts_process is False


def test_l4_phase5_resource_usage_descriptor_rejects_allocation():
    with pytest.raises(ValueError):
        ResourceUsageDescriptor(
            resource_usage_ref=phase5_ref(137, "resource_usage"),
            allocates_resource=True,
        )
