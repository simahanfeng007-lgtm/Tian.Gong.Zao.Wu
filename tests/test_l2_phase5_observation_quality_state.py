import inspect

from tiangong_kernel.l2_state import (
    ObservationQualityDimension,
    ObservationQualityState,
    ObservationQualityStatus,
)
from tests.test_l2_phase5_cross_phase_references import build_phase5_chain, identity, status


FORBIDDEN_METHODS = {"score_quality", "calculate_trust", "decide_reliability", "resolve_conflict"}


def test_l2_phase5_observation_quality_expresses_dimensions_and_statuses():
    for dimension in (
        ObservationQualityDimension.COMPLETENESS,
        ObservationQualityDimension.FRESHNESS,
        ObservationQualityDimension.CONSISTENCY,
        ObservationQualityDimension.REDACTION_SAFETY,
        ObservationQualityDimension.CONFLICT_LEVEL,
    ):
        state = ObservationQualityState(identity=identity(260), status=status(), quality_dimension=dimension)
        assert state.quality_dimension is dimension

    for quality_status in (
        ObservationQualityStatus.GOOD,
        ObservationQualityStatus.PARTIAL,
        ObservationQualityStatus.CONFLICTED,
        ObservationQualityStatus.UNSAFE,
        ObservationQualityStatus.UNKNOWN,
    ):
        state = ObservationQualityState(identity=identity(261), status=status(), quality_status=quality_status)
        assert state.quality_status is quality_status


def test_l2_phase5_observation_quality_records_evidence_without_algorithms():
    objects = build_phase5_chain()
    quality = objects["quality"]
    methods = {
        name
        for name, value in inspect.getmembers(ObservationQualityState, inspect.isfunction)
        if not name.startswith("__")
    }

    assert quality.evidence_frame_refs == (objects["frame"].identity.state_ref,)
    assert quality.boundary_state_refs == (objects["phase4"]["boundary_check"].identity.state_ref,)
    assert quality.security_state_refs == (objects["phase4"]["security"].identity.state_ref,)
    assert quality.quality_status is ObservationQualityStatus.PARTIAL
    assert FORBIDDEN_METHODS.isdisjoint(methods)
