from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives import stable_hash, stable_json_dumps, to_primitive
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.signal import SignalConfidence, SignalKind, SignalPolarity, SignalRef, SignalStrength, SignalWindow
from tiangong_kernel.l0_primitives.time import TemporalWindow, TimeRange, Timestamp


def test_signal_construction_immutability_serialization_and_hash():
    signal_ref = SignalRef(RefId("signal:" + "e" * 32))
    strength = SignalStrength(0.75)
    confidence = SignalConfidence(0.8)
    window = SignalWindow(TemporalWindow(TimeRange(Timestamp(10), Timestamp(20)), label="health"))
    assert to_primitive(strength)["value"] == 0.75
    assert stable_json_dumps((signal_ref, strength, confidence, window)) == stable_json_dumps((signal_ref, strength, confidence, window))
    assert stable_hash((signal_ref, strength, confidence, window)) == stable_hash((signal_ref, strength, confidence, window))
    try:
        strength.value = 0.1
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("SignalStrength allowed mutation")


def test_signal_enum_values_are_stable():
    assert [item.value for item in SignalKind] == [
        "health",
        "resource",
        "risk",
        "pressure",
        "feedback",
        "recovery",
        "adaptation",
        "drift",
        "damage",
        "retention",
        "decay",
        "reinforcement",
        "interference",
        "stability",
        "anomaly",
        "unknown",
    ]
    assert [item.value for item in SignalPolarity] == ["positive", "negative", "neutral", "mixed", "unknown"]
