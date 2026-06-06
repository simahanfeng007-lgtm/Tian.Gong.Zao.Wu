from l5_phase5_helpers import validate_all, valid_resource


def test_high_permission_cannot_bypass_budget():
    report = validate_all(resource_decls=(valid_resource(high_permission_budget_policy_ref="policy:bypass_budget"),))
    assert report.p0_count >= 1
