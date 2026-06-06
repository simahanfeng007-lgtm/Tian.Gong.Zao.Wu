from l5_phase3_sample_factory import complete_record, complete_snapshot, conflict_report
from tiangong_kernel.l5_plugin_host import public_projection_from_record


def test_public_projection_evidence_refs_are_redacted():
    record = complete_record(evidence_refs=("evidence:very_sensitive_internal_ref",))
    snapshot = complete_snapshot((record,))
    projection = public_projection_from_record(record, snapshot, conflict_report(snapshot))
    assert projection.evidence_refs == ("redacted:very_sensitive_internal",)
