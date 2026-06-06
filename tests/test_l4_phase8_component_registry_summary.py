import pytest

from l4_phase8_builders import component_registry_summary, phase8_ref
from tiangong_kernel.l4_execution import L4ComponentRegistrySummary


def test_l4_phase8_component_registry_summary_is_not_runtime_registry():
    summary = component_registry_summary()

    assert summary.summary_only is True
    assert summary.creates_runtime_registry is False
    assert summary.dynamically_loads_plugins is False
    assert summary.hosts_l6_subsystem is False
    assert ("l4_execution", "closure_summary") in summary.component_items


def test_l4_phase8_component_registry_summary_rejects_plugin_hosting():
    with pytest.raises(ValueError):
        L4ComponentRegistrySummary(
            component_registry_summary_ref=phase8_ref(120, "component_summary"),
            dynamically_loads_plugins=True,
        )
