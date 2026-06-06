import pytest

from l4_phase8_builders import no_boundary_bypass_guarantee, phase8_ref
from tiangong_kernel.l4_execution import L4NoBoundaryBypassGuarantee


def test_l4_phase8_no_boundary_bypass_guarantee_covers_l5_owned_boundaries():
    guarantee = no_boundary_bypass_guarantee()

    for boundary in ("permit", "policy", "risk", "confirmation", "lease", "credential"):
        assert boundary in guarantee.covered_boundaries
    assert guarantee.makes_policy_decision is False
    assert guarantee.makes_risk_decision is False
    assert guarantee.issues_permit is False
    assert guarantee.generates_confirmation_ticket is False
    assert guarantee.grants_lease is False
    assert guarantee.resolves_credential is False
    assert guarantee.authorizes_concurrency is False


def test_l4_phase8_no_boundary_bypass_guarantee_rejects_authority_flags():
    with pytest.raises(ValueError):
        L4NoBoundaryBypassGuarantee(guarantee_ref=phase8_ref(150, "no_boundary_bypass"), issues_permit=True)
