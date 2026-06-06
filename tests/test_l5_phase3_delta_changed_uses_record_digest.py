from l5_phase3_sample_factory import complete_record, complete_snapshot
from tiangong_kernel.l5_plugin_host import build_registry_delta


def test_delta_changed_uses_canonical_record_digest_not_object_identity():
    base = complete_record(summary="base")
    target = complete_record(summary="target")
    delta = build_registry_delta("delta:digest", complete_snapshot((base,)), complete_snapshot((target,)))
    assert delta.changed[0].base_record_digest == base.canonical_record_digest
    assert delta.changed[0].target_record_digest == target.canonical_record_digest
    assert "summary" in delta.changed[0].changed_fields
