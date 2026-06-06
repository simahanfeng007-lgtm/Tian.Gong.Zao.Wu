import pytest

from tiangong_kernel.l6_plugins.common import L6PluginManifest, L6PublicProjection, public_projection_from_manifest


def test_l6_manifest_rejects_live_locator_and_secret_like_values():
    with pytest.raises(ValueError):
        L6PluginManifest(plugin_id="l6.bad", plugin_name="bad https://api.example.invalid", plugin_version="0.1.0")
    with pytest.raises(ValueError):
        L6PluginManifest(plugin_id="l6.bad", plugin_name="bad api_key=plain", plugin_version="0.1.0")
    with pytest.raises(ValueError):
        L6PluginManifest(plugin_id="l6.bad", plugin_name="bad", plugin_version="0.1.0", l5_registry_ref="/tmp/registry.json")


def test_l6_manifest_is_not_l5_host_or_parallel_runtime():
    manifest = L6PluginManifest(plugin_id="l6.safe", plugin_name="safe", plugin_version="0.1.0")
    assert manifest.l5_host_binding_ref
    assert manifest.l5_governance_binding_ref
    assert manifest.public_projection_policy_ref
    assert manifest.forbidden_imports
    assert manifest.forbidden_network_targets
    assert manifest.tests_required


def test_l6_public_projection_minimal_disclosure_rejects_leaks():
    with pytest.raises(ValueError):
        L6PublicProjection(status_summary="token=plain")
    with pytest.raises(ValueError):
        L6PublicProjection(status_summary="shell subprocess requested")
    manifest = L6PluginManifest(plugin_id="l6.safe_projection", plugin_name="safe", plugin_version="0.1.0")
    projection = public_projection_from_manifest(manifest)
    assert projection.contains_raw_credential is False
    assert projection.contains_external_endpoint is False
    assert projection.contains_complete_internal_plan is False
