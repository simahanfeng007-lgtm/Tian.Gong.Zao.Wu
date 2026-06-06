from dataclasses import FrozenInstanceError, fields, is_dataclass

import pytest

from l2_phase8_builders import build_component_compatibility_objects, identity, status
from tiangong_kernel.l2_state import (
    ComponentCompatibilityStatus,
    ComponentStatus,
    CompatibilityStatus,
    L2ComponentHealthState,
    L2StateKind,
    LegacyMappingState,
)


def test_l2_phase8_component_and_compatibility_objects_are_frozen_slots_dataclasses():
    for name, item in build_component_compatibility_objects().items():
        assert is_dataclass(item), name
        assert getattr(type(item), "__slots__", None) is not None, name
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "changed"  # type: ignore[misc]


def test_l2_phase8_component_and_compatibility_objects_have_identity_status_schema():
    for name, item in build_component_compatibility_objects().items():
        field_names = {field.name for field in fields(item)}
        assert {"identity", "status", "schema_version"}.issubset(field_names), name
        assert item.schema_version == "0.1", name


def test_l2_phase8_component_health_rejects_negative_issue_count():
    with pytest.raises(ValueError):
        L2ComponentHealthState(identity=identity(900, L2StateKind.COMPONENT), status=status(), issue_count=-1)


def test_l2_phase8_legacy_mapping_rejects_invalid_confidence_hint():
    with pytest.raises(ValueError):
        LegacyMappingState(identity=identity(901, L2StateKind.COMPATIBILITY), status=status(), confidence_hint=1.5)


def test_l2_phase8_status_enums_keep_state_only_semantics():
    assert ComponentStatus.AVAILABLE.value == "available"
    assert ComponentCompatibilityStatus.COMPATIBLE.value == "compatible"
    assert CompatibilityStatus.MIGRATION_NEEDED.value == "migration_needed"
