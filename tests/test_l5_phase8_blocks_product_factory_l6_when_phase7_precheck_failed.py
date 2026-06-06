from tiangong_kernel.l5_plugin_host import GENERIC_HOST_BLOCK_TOOL_ONLY
from tests.l5_phase8_factories import passing_quality_gate


def test_l5_phase8_blocks_product_factory_l6_when_phase7_precheck_failed():
    gate = passing_quality_gate(generic_plugin_host_precheck_result=GENERIC_HOST_BLOCK_TOOL_ONLY)
    assert gate.allow_freeze_l5 is True
    assert gate.allow_enter_l6_general_plugins is True
    assert gate.allow_enter_l6_product_artifact_factory is False
