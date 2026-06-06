import pytest

from tiangong_kernel.l5_plugin_host import (
    L5Phase1BlockingFinding,
    L5Phase1NonBlockingFinding,
    L5Phase1QualityGateDecision,
    L5Phase1QualityGateSummary,
)


def test_quality_gate_decision_allows_next_phase_only_without_blocking_findings():
    decision = L5Phase1QualityGateDecision(
        gate_id="quality_gate:phase1",
        baseline_refs=("baseline:pre_l5",),
        required_checks=("compileall", "full_pytest", "forbidden_scan"),
        observed_results=("compileall passed", "full pytest passed", "forbidden scan passed"),
        non_blocking_findings=(L5Phase1NonBlockingFinding(finding_ref="finding:p3_zip_count", reason="归档条目数口径差异。"),),
        decision="allow_next_phase",
        reason="全部阻断项为零。",
        recorded_at="2026-06-04T09:00:00+08:00",
    )
    assert decision.decision == "allow_next_phase"


def test_quality_gate_blocks_when_blocking_finding_exists():
    finding = L5Phase1BlockingFinding(finding_ref="finding:p0", reason="阻断项。")
    with pytest.raises(ValueError):
        L5Phase1QualityGateSummary(
            gate_id="quality_gate:phase1",
            blocking_findings=(finding,),
            decision="allow_next_phase",
        )
    blocked = L5Phase1QualityGateSummary(
        gate_id="quality_gate:phase1",
        blocking_findings=(finding,),
        decision="block_next_phase",
        reason="存在阻断项。",
    )
    assert blocked.decision == "block_next_phase"
