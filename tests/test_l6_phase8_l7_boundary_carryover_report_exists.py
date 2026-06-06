from tiangong_kernel.l6_plugins.final_closure import L7BoundaryCarryoverReport

def test_l7_boundary_carryover_report_exists():
    assert L7BoundaryCarryoverReport().object_ref == 'report:l6_phase8_l7_boundary_carryover'
