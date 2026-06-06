from tiangong_kernel.l5_plugin_host import L5FinalPublicProjection, L5FinalPublicProjectionBuilder
from tests.l5_phase8_factories import passing_quality_gate


def test_l5_phase8_final_public_projection_redacted_evidence_refs():
    projection = L5FinalPublicProjection(redacted_evidence_refs=("evidence:redacted:final",))
    assert projection.redacted_evidence_refs == ("evidence:redacted:final",)


def test_l5_phase8_final_public_projection_builder_redacts_quality_gate_evidence_refs():
    projection = L5FinalPublicProjectionBuilder().make_projection(quality_gate=passing_quality_gate())
    assert projection.redacted_evidence_refs == ("evidence:redacted:l5_final_quality_gate",)
    assert not hasattr(projection, "evidence_ref")
