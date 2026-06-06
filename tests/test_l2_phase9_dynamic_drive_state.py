from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from l2_phase9_builders import build_dynamic_drive_objects
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l2_state import DynamicDriveKind, ExecutionReadinessState


def test_l2_phase9_dynamic_drive_objects_are_frozen_slots_and_serializable():
    for name, item in build_dynamic_drive_objects().items():
        assert is_dataclass(item), name
        assert hasattr(type(item), "__slots__"), name
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "x"
        assert stable_json_dumps(item), name
        assert len(stable_hash(item)) == 64, name


def test_l2_phase9_dynamic_drive_enums_keep_expected_values():
    assert DynamicDriveKind.EXPLORATION.value == "exploration"
    assert DynamicDriveKind.RECOVERY.value == "recovery"
    assert DynamicDriveKind.MINIMAL_EXPOSURE.value == "minimal_exposure"
    assert DynamicDriveKind.USER_ALIGNMENT.value == "user_alignment"
    assert DynamicDriveKind.UNKNOWN.value == "unknown"


def test_l2_phase9_execution_readiness_is_reference_state_only():
    readiness = build_dynamic_drive_objects()["readiness"]
    assert isinstance(readiness, ExecutionReadinessState)
    assert readiness.required_boundary_refs
    assert readiness.required_execution_refs
    assert readiness.missing_requirements == ("boundary_review",)
    assert not hasattr(readiness, "call_tool")
    assert not hasattr(readiness, "release_tool")
