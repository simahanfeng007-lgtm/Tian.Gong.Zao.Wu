from l5_phase3_sample_factory import complete_record, complete_snapshot
from tiangong_kernel.l5_plugin_host import build_registry_delta, registry_canonical_payload


def test_snapshot_and_delta_digest_exclude_self_and_volatile_fields():
    snapshot = complete_snapshot((complete_record(),))
    payload = registry_canonical_payload(snapshot)
    assert "snapshot_digest" not in payload
    assert "registry_digest" not in payload
    delta = build_registry_delta("delta:test", snapshot, complete_snapshot((complete_record(summary="changed"),)))
    delta_payload = registry_canonical_payload(delta)
    assert "delta_digest" not in delta_payload
    assert delta.delta_digest
