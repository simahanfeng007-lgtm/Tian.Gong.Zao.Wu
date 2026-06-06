import pytest
from tiangong_kernel.l6_plugins.final_closure import L6CrossPhaseCompatibilityMatrix

def test_cross_phase_compatibility_matrix_exists():
    assert L6CrossPhaseCompatibilityMatrix().common_contract_compatible is True
    with pytest.raises(ValueError):
        L6CrossPhaseCompatibilityMatrix(common_contract_compatible=False)
