import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_no_plugin_direct_import_call_state_write():
    for decl in default_governance_control_plugin_declarations():
        assert decl.direct_plugin_link is False
    bad = scan_l6_phase5_text('test:l6_phase5_bad_link', 'direct_event_queue direct_model_client plugin_instance')
    assert bad.passed is False
