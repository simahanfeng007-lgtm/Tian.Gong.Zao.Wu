import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_interoperation_host_mediated_only():
    matrix = default_phase4_interoperation_matrix()
    assert matrix
    assert all(rule.host_mediated_only for rule in matrix)
    assert all(rule.direct_import_allowed is False for rule in matrix)
    assert all(rule.direct_call_allowed is False for rule in matrix)
    with pytest.raises(ValueError):
        Phase4InteroperationRule(
            rule_ref="l6:bad_rule",
            source_plugin_ref="l6_phase4:a",
            target_plugin_ref="l6_phase4:b",
            channel=Phase4CollaborationChannel.EVENT,
            output_refs=("projection:l6_phase4_x",),
            direct_call_allowed=True,
        )
