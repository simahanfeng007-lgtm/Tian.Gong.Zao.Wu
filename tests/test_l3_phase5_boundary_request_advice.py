from l3_phase5_builders import build_l3_phase5_objects
from tiangong_kernel.l3_orchestration import (
    BoundaryCheckEnvelope,
    BoundaryCheckRequest,
    BoundaryReviewAdvice,
    ConfirmationRequest,
    LeaseRequest,
    PermissionReviewRequest,
    RiskReviewRequest,
)


def test_boundary_request_family_is_request_only_not_decision():
    objects = build_l3_phase5_objects()
    request = objects["boundary_request"]
    envelope = objects["boundary_envelope"]
    assert isinstance(request, BoundaryCheckRequest)
    assert isinstance(envelope, BoundaryCheckEnvelope)
    assert request.request_only is True
    assert envelope.request_only is True
    assert not hasattr(request, "policy_decision")
    assert not hasattr(request, "permission_decision")
    assert not hasattr(request, "risk_decision")


def test_risk_permission_confirmation_and_lease_requests_are_pure_requests():
    objects = build_l3_phase5_objects()
    assert isinstance(objects["risk_request"], RiskReviewRequest)
    assert isinstance(objects["permission_request"], PermissionReviewRequest)
    assert isinstance(objects["confirmation_request"], ConfirmationRequest)
    assert isinstance(objects["lease_request"], LeaseRequest)
    assert objects["risk_request"].request_only is True
    assert objects["permission_request"].request_only is True
    assert objects["confirmation_request"].request_only is True
    assert objects["lease_request"].request_only is True
    assert not hasattr(objects["confirmation_request"], "ticket")
    assert not hasattr(objects["lease_request"], "granted_lease")


def test_boundary_review_advice_does_not_perform_l5_review():
    objects = build_l3_phase5_objects()
    advice = objects["boundary_review"]
    assert isinstance(advice, BoundaryReviewAdvice)
    assert advice.advisory_only is True
    assert advice.preparation_advice is objects["boundary_prep"]
    assert not hasattr(advice, "review_result")
    assert not hasattr(advice, "submit")
