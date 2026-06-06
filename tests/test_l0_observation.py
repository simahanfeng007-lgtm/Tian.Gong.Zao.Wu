from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives import stable_hash, stable_json_dumps, to_primitive
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.observation import (
    ObservationKind,
    ObservationPayloadRef,
    ObservationQuality,
    ObservationRef,
    ObservationSource,
    ObservationWindow,
)
from tiangong_kernel.l0_primitives.time import TemporalWindow, TimeRange, Timestamp


def test_observation_construction_immutability_serialization_and_hash():
    window = ObservationWindow(TemporalWindow(TimeRange(Timestamp(1), Timestamp(2)), label="raw"))
    source = ObservationSource(source_kind="test", trust_boundary="local")
    payload_ref = ObservationPayloadRef(RefId("payload:" + "c" * 32), payload_type="message")
    observation_ref = ObservationRef(RefId("observation:" + "d" * 32))
    assert to_primitive(window)["window"]["label"] == "raw"
    assert to_primitive(source)["trust_boundary"] == "local"
    assert to_primitive(payload_ref)["payload_type"] == "message"
    assert stable_json_dumps(observation_ref) == stable_json_dumps(observation_ref)
    assert stable_hash((window, source, payload_ref, observation_ref)) == stable_hash((window, source, payload_ref, observation_ref))
    try:
        observation_ref.schema_version = "0.2"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("ObservationRef allowed mutation")


def test_observation_enum_values_are_stable():
    assert [item.value for item in ObservationKind] == ["message", "event", "state", "effect", "metric", "signal", "content", "unknown"]
    assert [item.value for item in ObservationQuality] == ["raw", "partial", "normalized", "conflicted", "low_confidence", "unknown"]
