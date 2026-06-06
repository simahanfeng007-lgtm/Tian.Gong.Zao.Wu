import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import HandoffAggregationCandidate

def test_handoff_aggregation_not_auto_merge():
    item = HandoffAggregationCandidate()
    assert item.auto_merges is False
    with pytest.raises(ValueError):
        HandoffAggregationCandidate(auto_merges=True)
