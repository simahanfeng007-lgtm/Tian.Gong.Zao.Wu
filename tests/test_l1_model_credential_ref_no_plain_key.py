import pytest
from tiangong_kernel.l1_ports.model_provider_governance_ports import ModelCredentialRequirementRef


def test_l1_credential_ref_rejects_plain_secret():
    with pytest.raises(ValueError):
        ModelCredentialRequirementRef("sk-demo-secret")
    assert ModelCredentialRequirementRef("cred-handle:openai-prod").credential_handle_ref.startswith("cred-handle")
