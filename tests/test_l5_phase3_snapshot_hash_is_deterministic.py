from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_key


def test_snapshot_hash_is_stable_across_input_order():
    a = complete_record(registry_record_ref="record:a")
    b = complete_record(registry_record_ref="record:b", registry_key=registry_key("plugin:b", "version:2"), manifest_hash="b"*64, manifest_digest_value="b"*64, plugin_version_ref="version:2")
    first = complete_snapshot((b, a))
    second = complete_snapshot((a, b))
    assert first.snapshot_digest == second.snapshot_digest
