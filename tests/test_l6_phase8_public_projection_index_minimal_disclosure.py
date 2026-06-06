import pytest
from tiangong_kernel.l6_plugins.final_closure import L6PublicProjectionIndex

def test_public_projection_index_minimal_disclosure():
    assert L6PublicProjectionIndex().minimal_disclosure is True
    with pytest.raises(ValueError):
        L6PublicProjectionIndex(contains_sensitive_detail=True)
