import pytest

from l5_phase3_sample_factory import registry_key, registry_namespace, registry_scope
from tiangong_kernel.l5_plugin_host import PluginRegistryKey


def test_registry_key_namespace_scope_are_declarations():
    key = registry_key()
    namespace = registry_namespace()
    scope = registry_scope()
    assert key.key_text == "namespace:user_declared|plugin:l5_phase3_demo|declaration|version:1"
    assert namespace.uniqueness_policy == "multi_version_allowed"
    assert scope.visible_to_refs == ("actor:l5_engineer",)


def test_registry_key_rejects_executable_entry_ref():
    with pytest.raises(ValueError):
        PluginRegistryKey(plugin_id="plugin:x", namespace="namespace:x", plugin_kind="declaration", version_ref="version:1", entry_ref="pkg.mod:function")
