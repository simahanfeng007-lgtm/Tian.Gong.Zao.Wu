from tiangong_kernel.l6_plugins.adaptive_collaboration import ConflictResolutionSuggestion

def test_conflict_suggestion_should_not_decide():
    assert ConflictResolutionSuggestion().final_decision is False
