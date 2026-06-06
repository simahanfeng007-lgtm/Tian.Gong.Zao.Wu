import pytest
from tiangong_kernel.l6_plugins.product_delivery import *

def test_artifact_structure_candidate_not_file_tree():
    artifact = ArtifactStructureCandidate()
    assert artifact.real_file_tree is False
    with pytest.raises(ValueError):
        ArtifactStructureCandidate(real_file_tree=True)
