from tiangong_kernel.l6_plugins.final_closure import L6UnifiedForbiddenScanRuleSet

def test_unified_forbidden_scan_covers_phase1_to_phase7():
    rules = L6UnifiedForbiddenScanRuleSet()
    assert len(rules.scan_scope_refs) >= 8
    assert rules.inert_pattern_only is True
