from l5_phase3_sample_factory import complete_record, complete_snapshot, conflict_report
from tiangong_kernel.l5_plugin_host import public_projection_from_record


def test_public_projection_credential_summary_is_minimal_and_redacted():
    record = complete_record(credential_decl_ref="credential_decl:internal_handle_ref")
    projection = public_projection_from_record(record, complete_snapshot((record,)), conflict_report())
    assert projection.credential_summary.redaction_state == "redacted"
    assert not hasattr(projection.credential_summary, "raw_value")
    assert not hasattr(projection.credential_summary, "credential_handle")
