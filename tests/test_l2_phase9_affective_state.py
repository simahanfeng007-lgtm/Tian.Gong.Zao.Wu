from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from l2_phase9_builders import build_affective_objects
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l2_state import AffectiveBoundaryState, DesireTendencyKind, EmotionKind


def test_l2_phase9_affective_objects_are_frozen_slots_and_serializable():
    for name, item in build_affective_objects().items():
        assert is_dataclass(item), name
        assert hasattr(type(item), "__slots__"), name
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "x"
        assert stable_json_dumps(item), name
        assert len(stable_hash(item)) == 64, name


def test_l2_phase9_affective_enums_keep_expected_values():
    assert EmotionKind.JOY.value == "joy"
    assert EmotionKind.CURIOSITY.value == "curiosity"
    assert DesireTendencyKind.EXPLORATION.value == "exploration"
    assert DesireTendencyKind.REPAIR.value == "repair"
    assert EmotionKind.UNKNOWN.value == "unknown"


def test_l2_phase9_affective_boundary_defaults_prevent_override():
    boundary = build_affective_objects()["boundary"]
    assert isinstance(boundary, AffectiveBoundaryState)
    assert boundary.cannot_execute is True
    assert boundary.cannot_override_l5 is True
    assert boundary.cannot_override_l4 is True
    assert boundary.cannot_access_secret is True
    assert boundary.cannot_raise_permission is True
