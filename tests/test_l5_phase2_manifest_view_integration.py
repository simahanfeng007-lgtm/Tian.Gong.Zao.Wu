from l5_phase2_sample_factory import complete_manifest
from tiangong_kernel.l5_plugin_host import to_l5_primitive


def test_manifest_like_payload_integrates_phase2_declarations_without_execution_fields():
    manifest = complete_manifest()
    primitive = to_l5_primitive(manifest)
    assert primitive["entry_ref"]["entry_ref"] == "entry:l5_phase2"
    assert primitive["permission_decl"]["permit_issued"] is False
    assert primitive["resource_decl"]["budget_consumed"] is False
