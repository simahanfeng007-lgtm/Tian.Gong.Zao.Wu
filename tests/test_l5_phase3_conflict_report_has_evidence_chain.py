from l5_phase3_sample_factory import complete_snapshot, conflict_report


def test_conflict_report_carries_required_evidence_chain_fields():
    report = conflict_report(complete_snapshot())
    assert report.rule_source_ref
    assert report.detected_by_ref
    assert report.trace_ref
    assert report.evidence_refs
    assert report.responsibility_chain_ref
