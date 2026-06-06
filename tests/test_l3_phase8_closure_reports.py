from l3_phase8_builders import build_l3_phase8_objects
from tiangong_kernel.l3_orchestration import L3ClosureCheckKind


def test_l3_phase8_closure_reports_are_passive_reports():
    objects = build_l3_phase8_objects()
    assert objects["closure_request"].request_only is True
    assert set(objects["closure_request"].requested_check_kinds) == set(L3ClosureCheckKind)
    assert objects["closure_result"].report_only is True
    assert objects["closure_result"].no_auto_fix is True
    assert objects["boundary_report"].report_only is True
    assert objects["import_report"].report_only is True
    assert objects["serialization_report"].report_only is True
    assert objects["snapshot_report"].report_only is True
    assert objects["freeze_report"].report_only is True
    assert objects["freeze_report"].readiness_score == 1.0


def test_l3_phase8_guarantee_reports_remain_non_executing_non_deciding_non_subsystem():
    objects = build_l3_phase8_objects()
    assert "no_model_call" in objects["no_execution_report"].guarantee_items
    assert "no_permission_result" in objects["no_decision_report"].guarantee_items
    assert "no_learning_service" in objects["no_subsystem_report"].guarantee_items
    assert objects["no_execution_report"].report_only is True
    assert objects["no_decision_report"].report_only is True
    assert objects["no_subsystem_report"].report_only is True
