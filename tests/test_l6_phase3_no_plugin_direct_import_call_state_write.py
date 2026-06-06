import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_no_plugin_direct_import_call_or_state_write():
    matrix = default_mind_interoperation_matrix()
    assert matrix.event_projection_handoff_only_collaboration is True
    assert L6Phase3MindQualityGateDecision(no_plugin_direct_import_call_state_write_passed=False).allow_enter_phase4 is False
    with pytest.raises(ValueError):
        MindInteroperationMatrix(direct_call_allowed=True)
    with pytest.raises(ValueError):
        MindPluginDeclaration(plugin_ref="mind:bad", plugin_kind=MindPluginKind.CONTEXT, summary="bad", direct_plugin_link=True)
