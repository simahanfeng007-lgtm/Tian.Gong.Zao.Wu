from l5_phase3_sample_factory import complete_snapshot, conflict_report, quality_gate


def test_registry_quality_gate_passes_clean_snapshot_and_report():
    snapshot = complete_snapshot()
    report = conflict_report(snapshot)
    result = quality_gate().evaluate(snapshot, report)
    assert result.passed
    assert result.p0_count == 0
    assert result.p1_count == 0
