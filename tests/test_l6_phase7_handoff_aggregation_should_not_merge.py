from tiangong_kernel.l6_plugins.adaptive_collaboration import HandoffAggregationCandidate

def test_handoff_aggregation_should_not_merge():
    assert HandoffAggregationCandidate().auto_merges is False
