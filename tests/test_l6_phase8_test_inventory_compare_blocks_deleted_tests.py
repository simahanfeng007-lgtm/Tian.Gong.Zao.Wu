from tiangong_kernel.l6_plugins.final_closure import L6UnifiedTestInventoryCompareReport

def test_test_inventory_compare_blocks_deleted_tests():
    report = L6UnifiedTestInventoryCompareReport()
    assert report.freeze_candidate_flag is True
    assert report.planner_review_required is True
