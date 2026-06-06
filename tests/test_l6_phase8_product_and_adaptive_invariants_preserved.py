from tiangong_kernel.l6_plugins.final_closure import L6_PHASE8_INVARIANTS

def test_product_and_adaptive_invariants_preserved():
    names = set(L6_PHASE8_INVARIANTS)
    assert 'product_delivery_should_continue_when_low_risk' in names
    assert 'adaptive_failure_should_recover_not_abort' in names
    assert 'delivery_package_candidate_is_not_zip' in names
    assert 'repair_plan_candidate_is_not_code_patch' in names
