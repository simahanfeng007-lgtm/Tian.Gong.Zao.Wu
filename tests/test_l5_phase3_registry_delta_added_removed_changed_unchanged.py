from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_key
from tiangong_kernel.l5_plugin_host import build_registry_delta


def test_delta_describes_added_removed_changed_unchanged():
    unchanged_base = complete_record(registry_record_ref="record:unchanged")
    changed_base = complete_record(registry_record_ref="record:changed", registry_key=registry_key("plugin:changed", "version:1"))
    changed_target = complete_record(registry_record_ref="record:changed", registry_key=registry_key("plugin:changed", "version:1"), summary="changed summary")
    removed = complete_record(registry_record_ref="record:removed", registry_key=registry_key("plugin:removed", "version:1"))
    added = complete_record(registry_record_ref="record:added", registry_key=registry_key("plugin:added", "version:1"))
    delta = build_registry_delta("delta:test", complete_snapshot((unchanged_base, changed_base, removed)), complete_snapshot((unchanged_base, changed_target, added)))
    assert len(delta.added) == 1
    assert len(delta.removed) == 1
    assert len(delta.changed) == 1
    assert len(delta.unchanged) == 1
