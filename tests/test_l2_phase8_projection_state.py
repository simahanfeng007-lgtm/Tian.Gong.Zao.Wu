from dataclasses import FrozenInstanceError, fields, is_dataclass

import pytest

from l2_phase8_builders import build_projection_objects, identity, status
from tiangong_kernel.l2_state import (
    L2StateKind,
    ModelVisibleStateProjection,
    ProjectionAudience,
    ProjectionFragmentState,
    ProjectionStatus,
    ProjectionVisibility,
)


def test_l2_phase8_projection_objects_are_frozen_slots_dataclasses():
    for name, item in build_projection_objects().items():
        assert is_dataclass(item), name
        assert getattr(type(item), "__slots__", None) is not None, name
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "changed"  # type: ignore[misc]


def test_l2_phase8_projection_objects_have_identity_status_schema():
    for name, item in build_projection_objects().items():
        field_names = {field.name for field in fields(item)}
        assert {"identity", "status", "schema_version"}.issubset(field_names), name
        assert item.schema_version == "0.1", name


def test_l2_phase8_model_visible_projection_is_reference_only_not_execution_authority():
    projection = build_projection_objects()["model_visible"]
    field_names = {field.name for field in fields(projection)}
    forbidden_authority_fields = {
        "execution_token",
        "permission_grant",
        "tool_release_payload",
        "prompt_text",
        "model_client",
        "tool_client",
    }
    assert projection.projection_status == ProjectionStatus.READY
    assert forbidden_authority_fields.isdisjoint(field_names)
    assert projection.tool_group_refs


def test_l2_phase8_projection_fragment_rejects_long_title():
    with pytest.raises(ValueError):
        ProjectionFragmentState(identity=identity(920, L2StateKind.PROJECTION), status=status(), title="x" * 129)


def test_l2_phase8_projection_enums_keep_state_projection_semantics():
    assert ProjectionAudience.MODEL.value == "model"
    assert ProjectionVisibility.SUMMARY_ONLY.value == "summary_only"
    assert ProjectionStatus.READY.value == "ready"
    assert ModelVisibleStateProjection.__doc__
