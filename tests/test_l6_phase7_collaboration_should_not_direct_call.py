from tiangong_kernel.l6_plugins.adaptive_collaboration import MultiPluginCollaborationPlanCandidate

def test_collaboration_should_not_direct_call():
    assert MultiPluginCollaborationPlanCandidate().host_mediated_only is True
