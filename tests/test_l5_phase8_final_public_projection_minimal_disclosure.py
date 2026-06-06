import pytest
from tiangong_kernel.l5_plugin_host import L5FinalPublicProjection


def test_l5_phase8_final_public_projection_minimal_disclosure():
    projection = L5FinalPublicProjection()
    assert projection.redaction_state == "redacted"
    with pytest.raises(ValueError):
        L5FinalPublicProjection(handoff_summary=(("endpoint", "https://live.example/run"),))


@pytest.mark.parametrize(
    "summary",
    (
        (("path", "/mnt/data/output.zip"),),
        (("path", r"C:\Users\Admin\Desktop\key.txt"),),
        (("endpoint", "internal_service"),),
        (("handler", "x"),),
        (("module_path", "x"),),
        (("raw_credential", "x"),),
        (("raw_manifest", "{plugin_id:x}"),),
        (("plaintext_user_identity", "Alice Zhang"),),
        (("note", "sk-1234567890abcdef"),),
        (("note", "Bearer abcdef"),),
        (("note", "password=123456"),),
    ),
)
def test_l5_phase8_final_public_projection_rejects_dangerous_keys_and_values(summary):
    with pytest.raises(ValueError):
        L5FinalPublicProjection(test_summary=summary)


def test_l5_phase8_final_public_projection_requires_redacted_evidence_refs():
    with pytest.raises(ValueError):
        L5FinalPublicProjection(redacted_evidence_refs=())
    with pytest.raises(ValueError):
        L5FinalPublicProjection(redacted_evidence_refs=("evidence:l5_final_quality_gate",))
