import pytest

from tiangong_kernel.l5_plugin_host import AffectivePublicProjectionSummary, L5FinalPublicProjection


def test_affective_public_projection_minimal_disclosure():
    projection = AffectivePublicProjectionSummary()
    assert projection.redacted_evidence_refs == ("evidence:redacted:l5_affective_projection",)
    assert projection.redaction_state_ref
    assert projection.no_sensitive_profile_plaintext_ref


def test_affective_public_projection_rejects_live_locator_and_non_redacted_evidence():
    with pytest.raises(ValueError):
        AffectivePublicProjectionSummary(status_ref="https://example.invalid/affective")
    with pytest.raises(ValueError):
        AffectivePublicProjectionSummary(redacted_evidence_refs=("evidence:l5_affective_projection",))


def test_final_public_projection_contains_affective_summary_refs_only():
    projection = L5FinalPublicProjection()
    rows = dict(projection.affective_plugin_readiness_summary)
    assert rows["status"] == "l6_planning_only"
    assert rows["execution"] == "forbidden"
    assert rows["projection"] == "redacted_refs_only"
    assert projection.redaction_state == "redacted"
