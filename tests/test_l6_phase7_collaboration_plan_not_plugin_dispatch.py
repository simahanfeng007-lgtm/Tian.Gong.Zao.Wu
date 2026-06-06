import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import MultiPluginCollaborationPlanCandidate

def test_collaboration_plan_not_plugin_dispatch():
    item = MultiPluginCollaborationPlanCandidate()
    assert item.dispatches_plugins is False
    with pytest.raises(ValueError):
        MultiPluginCollaborationPlanCandidate(dispatches_plugins=True)
