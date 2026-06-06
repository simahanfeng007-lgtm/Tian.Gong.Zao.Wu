import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import ConflictResolutionSuggestion

def test_conflict_resolution_not_decision():
    item = ConflictResolutionSuggestion()
    assert item.final_decision is False
    with pytest.raises(ValueError):
        ConflictResolutionSuggestion(final_decision=True)
