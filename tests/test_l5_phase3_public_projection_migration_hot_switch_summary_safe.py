from l5_phase3_sample_factory import complete_record, complete_snapshot, conflict_report
from tiangong_kernel.l5_plugin_host import public_projection_from_record


def test_public_projection_migration_hot_switch_summaries_are_safe():
    record = complete_record()
    projection = public_projection_from_record(record, complete_snapshot((record,)), conflict_report())
    assert projection.migration_summary.ref == record.migration_ref
    assert projection.hot_switch_summary.ref == record.hot_switch_decl_ref
    assert "execute" not in projection.hot_switch_summary.summary.lower()
    assert projection.breaking_change_summary.evidence.startswith("redacted:")
