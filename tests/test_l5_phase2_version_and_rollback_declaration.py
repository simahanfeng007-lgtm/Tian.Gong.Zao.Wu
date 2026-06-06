import pytest

from tiangong_kernel.l5_plugin_host import PluginRollbackDeclaration, PluginVersionDeclaration


def test_version_and_rollback_are_declarative_only():
    version = PluginVersionDeclaration(
        plugin_version="1.0.0",
        api_version="1.0.0",
        schema_version_text="0.2",
        compatibility_range="0.2.x",
        migration_ref="migration:none",
        version_slot_ref="slot:declared",
    )
    rollback = PluginRollbackDeclaration(rollback_anchor_ref="rollback:anchor", rollback_policy_ref="rollback:policy")
    assert version.version_slot_ref == "slot:declared"
    assert rollback.tombstone_required
    with pytest.raises(ValueError):
        PluginVersionDeclaration(plugin_version="1.0.0", api_version="1.0.0", schema_version_text="0.2", hot_switch_executed=True)
    with pytest.raises(ValueError):
        PluginRollbackDeclaration(rollback_executed=True)
