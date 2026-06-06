import pytest

from tiangong_kernel.l5_plugin_host import L5GovernanceCoverageMatrix, L5GovernanceCoverageMatrixValidator


def test_l5_phase8_governance_coverage_matrix_covers_required_gates():
    matrix = L5GovernanceCoverageMatrix()
    assert len(matrix.governance_gate_refs) >= 14
    assert "gate:event" in matrix.governance_gate_refs
    assert "gate:artifact_provenance_integrity" in matrix.governance_gate_refs
    assert "gate:context_safety_boundary" in matrix.governance_gate_refs
    assert "gate:message_envelope_first" in matrix.governance_gate_refs
    assert "gate:self_healing_recovery_plan" in matrix.governance_gate_refs
    assert L5GovernanceCoverageMatrixValidator().check(matrix)


def test_l5_phase8_governance_coverage_matrix_rejects_missing_or_partial_rows():
    with pytest.raises(ValueError):
        L5GovernanceCoverageMatrix(coverage_rows=(("ToolPlugin", "missing"),))
