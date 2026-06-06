from l5_phase3_sample_factory import complete_record
from tiangong_kernel.l5_plugin_host import PluginRegistryIndex


def test_registry_index_is_deterministic_and_lookup_only():
    a = complete_record(registry_record_ref="record:a")
    b = complete_record(registry_record_ref="record:b", registry_key=complete_record().registry_key.__class__(plugin_id="plugin:b", namespace="namespace:user_declared", plugin_kind="declaration", version_ref="version:2", entry_ref="entry:b"), source_trust_ref="source_trust:b", version_slot_ref="slot:b")
    index1 = PluginRegistryIndex(index_ref="index:test", records=(b, a))
    index2 = PluginRegistryIndex(index_ref="index:test", records=(b, a))
    assert index1.index_digest == index2.index_digest
    assert index1.by_plugin_id("plugin:b") == (b,)
    assert index1.by_source_trust_ref("source_trust:b") == (b,)
