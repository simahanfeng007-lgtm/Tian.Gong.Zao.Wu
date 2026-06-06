from tiangong_kernel.l6_plugins.adaptive_collaboration import L6Phase7ForbiddenScanRuleSet, L6_PHASE7_FORBIDDEN_PATTERNS

def test_forbidden_scan_blocks_self_execution_patterns():
    rules = L6Phase7ForbiddenScanRuleSet()
    assert rules.passed is True
    for token in ('write_skill', 'auto_repair', 'merge_handoff_results', 'resolve_conflict_now'):
        assert token in L6_PHASE7_FORBIDDEN_PATTERNS
