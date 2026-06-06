from __future__ import annotations

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l3_orchestration.forgetting_service_request import (
    DecayPressureScore,
    DecayReviewAdvice,
    DeletionTombstoneAdvice,
    ForgettingServiceRequest,
    ForgettingServiceRequestRef,
    InterferencePressureScore,
    MemoryPrivacyReviewAdvice,
    PruningAdvice,
    PruningSuitabilityScore,
    RetentionReviewAdvice,
    RevisionNeedScore,
    SuppressionAdvice,
)


def _ref(suffix: int, ref_type: str = "forgetting") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_l3_forgetting_request_and_advice_are_advisory_only() -> None:
    request_ref = ForgettingServiceRequestRef(_ref(1))
    retention = RetentionReviewAdvice(_ref(2), memory_refs=(_ref(3),))
    decay = DecayReviewAdvice(_ref(4))
    suppression = SuppressionAdvice(_ref(5))
    pruning = PruningAdvice(_ref(6))
    tombstone = DeletionTombstoneAdvice(_ref(7), forgetting_ref=_ref(8), deletion_ref=_ref(9), tombstone_ref=_ref(10))
    privacy = MemoryPrivacyReviewAdvice(_ref(11), privacy_refs=(_ref(12),))
    request = ForgettingServiceRequest(
        request_ref,
        retention_reviews=(retention,),
        decay_reviews=(decay,),
        suppression_advices=(suppression,),
        pruning_advices=(pruning,),
        deletion_tombstone_advices=(tombstone,),
        privacy_reviews=(privacy,),
    )

    assert request.request_only is True
    for advice in (retention, decay, suppression, pruning, tombstone, privacy):
        assert advice.advisory_only is True
        assert advice.executes_forgetting is False
        assert advice.deletes_memory is False
        assert advice.no_memory_read is True

    with pytest.raises(ValueError):
        SuppressionAdvice(_ref(13), executes_forgetting=True)


def test_l3_forgetting_scores_are_externalized_not_formula_authority() -> None:
    scores = (
        DecayPressureScore(_ref(20), value=0.1, model_result_ref=_ref(21)),
        InterferencePressureScore(_ref(22), value=0.2),
        PruningSuitabilityScore(_ref(23), value=0.3),
        RevisionNeedScore(_ref(24), value=0.4),
    )

    for score in scores:
        assert score.externalized is True
        assert score.advisory_only is True
        assert score.no_hardcoded_formula is True

    with pytest.raises(ValueError):
        DecayPressureScore(_ref(25), value=1.5)
