from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives import stable_hash, stable_json_dumps, to_primitive
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.metric import (
    MetricAggregation,
    MetricKind,
    MetricPoint,
    MetricRef,
    MetricSeriesRef,
    MetricUnit,
    MetricValue,
    MetricWindow,
)
from tiangong_kernel.l0_primitives.time import TemporalWindow, TimeRange, Timestamp


def test_metric_construction_immutability_serialization_and_hash():
    metric_ref = MetricRef(RefId("metric:" + "f" * 32))
    point = MetricPoint(metric_ref, MetricKind.LATENCY, MetricValue(12.5), MetricUnit("ms"), Timestamp(100))
    series_ref = MetricSeriesRef(RefId("metric_series:" + "1" * 32), metric_kind=MetricKind.LATENCY)
    window = MetricWindow(TemporalWindow(TimeRange(Timestamp(90), Timestamp(110)), label="sample"))
    assert to_primitive(point)["kind"] == "latency"
    assert to_primitive(point)["aggregation"] == "point"
    assert stable_json_dumps((point, series_ref, window)) == stable_json_dumps((point, series_ref, window))
    assert stable_hash((point, series_ref, window)) == stable_hash((point, series_ref, window))
    try:
        point.value = MetricValue(1)
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("MetricPoint allowed mutation")


def test_metric_enum_values_are_stable():
    assert [item.value for item in MetricKind] == [
        "latency",
        "count",
        "rate",
        "ratio",
        "size",
        "capacity",
        "usage",
        "error",
        "throughput",
        "cost",
        "quality",
        "confidence",
        "unknown",
    ]
    assert MetricAggregation.MEAN.value == "mean"
