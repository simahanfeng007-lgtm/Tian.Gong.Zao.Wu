from l5_phase5_helpers import valid_projection


def test_public_projection_uses_only_redacted_summaries():
    projection = valid_projection()
    assert projection.redacted_evidence_refs
    text = str(projection)
    forbidden = ("raw_value", "token_value", "secret_value", "api_key_value", "password_value", "database_uri", "module:function")
    assert not any(item in text for item in forbidden)
