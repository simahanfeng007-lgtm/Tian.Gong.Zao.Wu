from l5_phase3_sample_factory import complete_record, complete_snapshot, conflict_report
from tiangong_kernel.l5_plugin_host import public_projection_from_record


def test_public_projection_does_not_expose_secret_or_entry_object():
    record = complete_record()
    snapshot = complete_snapshot((record,))
    projection = public_projection_from_record(record, snapshot, conflict_report(snapshot))
    text = repr(projection)
    assert "credential_handle" not in text
    assert "raw_value" not in text
    assert all(ref.startswith("redacted:") for ref in projection.evidence_refs)
    assert projection.hot_switch_summary.summary.endswith("ref only")
