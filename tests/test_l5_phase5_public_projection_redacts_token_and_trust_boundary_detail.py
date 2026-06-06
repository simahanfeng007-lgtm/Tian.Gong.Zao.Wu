from l5_phase5_helpers import valid_projection


def test_projection_token_and_trust_boundary_are_summarized():
    projection = valid_projection()
    assert any(k == "token_scope_count" for k, _ in projection.capability_token_summary)
    assert any(k == "data_boundary_count" or k == "trust_boundary_digest" for k, _ in projection.trust_boundary_summary)
    assert "raw token" not in str(projection).lower()
