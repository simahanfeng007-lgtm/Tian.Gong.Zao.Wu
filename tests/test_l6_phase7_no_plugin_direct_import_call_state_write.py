from tiangong_kernel.l6_plugins.adaptive_collaboration import MultiPluginCollaborationPlanCandidate
import pytest

def test_no_plugin_direct_import_call_state_write():
    with pytest.raises(ValueError):
        MultiPluginCollaborationPlanCandidate(direct_plugin_call=True)
