import pytest

from l4_phase8_builders import closure_projection, final_freeze_readiness, final_quality_checklist, phase8_ref
from tiangong_kernel.l4_execution import L4ClosureProjection, L4FinalFreezeReadinessReport, L4FinalQualityChecklist


def test_l4_phase8_final_freeze_readiness_recommends_quality_not_l5_l6():
    readiness = final_freeze_readiness()
    checklist = final_quality_checklist()
    projection = closure_projection()

    assert "phase8_closure_handoff_freeze" in readiness.completed_phases
    assert readiness.report_only is True
    assert readiness.recommends_l4_quality_audit is True
    assert readiness.recommends_direct_l5_or_l6_development is False
    assert readiness.skips_l4_quality_audit is False
    assert readiness.enables_live_action is False
    assert {level for level, _ in checklist.checklist_items} == {"P0", "P1", "P2", "P3"}
    assert checklist.executes_quality_audit is False
    assert checklist.executes_repair_flow is False
    assert checklist.approves_l5_or_l6_start is False
    assert projection.projection_only is True
    assert projection.writes_l2_state is False
    assert projection.mutates_l3_plan is False
    assert projection.starts_l5_or_l6 is False


def test_l4_phase8_final_freeze_readiness_rejects_skip_or_start_flags():
    with pytest.raises(ValueError):
        L4FinalFreezeReadinessReport(readiness_report_ref=phase8_ref(200, "readiness"), skips_l4_quality_audit=True)
    with pytest.raises(ValueError):
        L4FinalQualityChecklist(quality_checklist_ref=phase8_ref(201, "quality"), approves_l5_or_l6_start=True)
    with pytest.raises(ValueError):
        L4ClosureProjection(closure_projection_ref=phase8_ref(202, "projection"), starts_l5_or_l6=True)
