from l5_phase3_sample_factory import complete_record, complete_snapshot
from tiangong_kernel.l5_plugin_host import registry_canonical_payload


def test_snapshot_canonical_serialization_is_dict_and_utf8_safe():
    snapshot = complete_snapshot((complete_record(summary="中文摘要"),))
    payload = registry_canonical_payload(snapshot)
    assert isinstance(payload, dict)
    assert payload["records"][0]["summary"] == "中文摘要"
