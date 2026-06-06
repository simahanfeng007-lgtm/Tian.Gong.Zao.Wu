import pytest

from l5_phase2_sample_factory import mutable_manifest_namespace, quality_gate
from tiangong_kernel.l5_plugin_host import PluginResourceDeclaration


def test_high_permission_cannot_bypass_resource_budget():
    with pytest.raises(ValueError):
        PluginResourceDeclaration(high_permission_does_not_bypass_budget=False)


def test_quality_gate_accepts_high_permission_only_when_budget_controls_exist():
    manifest = mutable_manifest_namespace()
    report = quality_gate().evaluate(manifest)
    assert report.passed
