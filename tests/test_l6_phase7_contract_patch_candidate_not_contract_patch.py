import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import ContractPatchCandidate

def test_contract_patch_candidate_not_contract_patch():
    item = ContractPatchCandidate()
    assert item.applies_contract_patch is False
    with pytest.raises(ValueError):
        ContractPatchCandidate(applies_contract_patch=True)
