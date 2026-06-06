from dataclasses import is_dataclass

from l3_phase8_builders import build_l3_phase8_objects
from tiangong_kernel.l3_orchestration import orchestration_stable_hash, orchestration_stable_json


PUBLIC_OBJECT_KEYS = (
    "component_index",
    "math_catalog",
    "projection",
    "l4_envelope",
    "l5_envelope",
    "l6_envelope",
    "closure_result",
    "freeze_report",
)


def test_l3_phase8_public_objects_are_frozen_slots_dataclasses():
    objects = build_l3_phase8_objects()
    for key in PUBLIC_OBJECT_KEYS:
        value = objects[key]
        assert is_dataclass(value)
        assert getattr(value, "__dataclass_params__").frozen is True
        assert hasattr(value, "__slots__")


def test_l3_phase8_stable_json_and_hash_are_repeatable():
    objects = build_l3_phase8_objects()
    for key in PUBLIC_OBJECT_KEYS:
        value = objects[key]
        assert orchestration_stable_json(value) == orchestration_stable_json(value)
        assert orchestration_stable_hash(value) == orchestration_stable_hash(value)
