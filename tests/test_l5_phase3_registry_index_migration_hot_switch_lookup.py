from l5_phase3_sample_factory import complete_record
from tiangong_kernel.l5_plugin_host import PluginRegistryIndex


def test_registry_index_supports_migration_hot_switch_and_version_lookup_dimensions():
    record = complete_record()
    index = PluginRegistryIndex(index_ref="index:l5_phase3", records=(record,))
    assert index.by_hot_switch_decl_ref(record.hot_switch_decl_ref) == (record,)
    assert index.by_migration_ref(record.migration_ref) == (record,)
    assert index.by_rollback_anchor_ref(record.rollback_anchor_ref) == (record,)
    assert index.by_replay_compatibility_ref(record.replay_compatibility_ref) == (record,)
    assert index.by_breaking_change_policy_ref(record.breaking_change_policy_ref) == (record,)
    assert index.by_schema_version(record.schema_version_text) == (record,)
    assert index.by_api_version(record.api_version) == (record,)
