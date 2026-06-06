from tiangong_kernel.l2_state import ObservationMetricKind, ObservationMetricState, ObservationMetricStatus
from tests.test_l2_phase5_cross_phase_references import build_phase5_chain, identity, status


def test_l2_phase5_observation_metric_expresses_kinds_and_statuses():
    for metric_kind in (
        ObservationMetricKind.LATENCY,
        ObservationMetricKind.TOKEN_USAGE,
        ObservationMetricKind.RESOURCE_PRESSURE,
        ObservationMetricKind.HEALTH_SIGNAL,
    ):
        state = ObservationMetricState(identity=identity(240), status=status(), metric_kind=metric_kind)
        assert state.metric_kind is metric_kind

    for metric_status in (
        ObservationMetricStatus.REPORTED,
        ObservationMetricStatus.PARTIAL,
        ObservationMetricStatus.REDACTED,
        ObservationMetricStatus.CONFLICTED,
    ):
        state = ObservationMetricState(identity=identity(241), status=status(), metric_status=metric_status)
        assert state.metric_status is metric_status


def test_l2_phase5_observation_metric_records_external_snapshot_without_sampling():
    objects = build_phase5_chain()
    metric = objects["metric"]

    assert metric.metric_name == "observed_latency"
    assert metric.metric_value_repr == "42ms"
    assert metric.metric_unit == "ms"
    assert metric.metric_window_ref is not None
    assert metric.related_resource_state_refs == (objects["phase4"]["budget"].identity.state_ref,)
    assert metric.quality_state_ref == objects["quality"].identity.state_ref
    assert not hasattr(metric, "sample")
    assert not hasattr(metric, "read_metric")
