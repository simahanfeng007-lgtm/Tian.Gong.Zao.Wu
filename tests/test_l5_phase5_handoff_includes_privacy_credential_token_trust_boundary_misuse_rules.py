from l5_phase5_helpers import valid_projection


def test_privacy_credential_token_trust_boundary_misuse_rules_are_represented_by_summaries():
    projection = valid_projection()
    assert projection.credential_summary
    assert projection.capability_token_summary
    assert projection.trust_boundary_summary
