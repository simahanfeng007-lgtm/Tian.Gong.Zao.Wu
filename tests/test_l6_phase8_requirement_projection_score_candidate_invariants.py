from tiangong_kernel.l6_plugins.final_closure import L6Phase8InvariantSuite, L6_PHASE8_INVARIANTS

def test_requirement_projection_score_candidate_invariants():
    names = set(L6_PHASE8_INVARIANTS)
    assert 'requirement_is_not_permit' in names
    assert 'projection_is_not_fact' in names
    assert 'score_is_not_decision' in names
    assert 'candidate_is_not_execution' in names
    assert len(L6Phase8InvariantSuite().invariant_refs) >= 66
