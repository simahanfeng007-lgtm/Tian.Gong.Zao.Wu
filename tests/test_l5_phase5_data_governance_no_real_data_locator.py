from l5_phase5_helpers import validate_all, valid_data_governance


def test_data_governance_rejects_database_uri():
    report = validate_all(data_governance_decls=(valid_data_governance(export_policy_ref="mysql://live/customer"),))
    assert report.p0_count >= 1
