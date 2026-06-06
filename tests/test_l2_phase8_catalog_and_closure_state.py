from dataclasses import FrozenInstanceError, fields, is_dataclass

import pytest

from l2_phase8_builders import build_catalog_closure_objects, identity, status
from tiangong_kernel.l2_state import (
    L2ClosureStatus,
    L2IssueSeverity,
    L2KnownIssueState,
    L2StateCatalog,
    L2StateKind,
    L2ValidationSummaryState,
)


def test_l2_phase8_catalog_and_closure_objects_are_frozen_slots_dataclasses():
    for name, item in build_catalog_closure_objects().items():
        assert is_dataclass(item), name
        assert getattr(type(item), "__slots__", None) is not None, name
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "changed"  # type: ignore[misc]


def test_l2_phase8_catalog_and_closure_objects_have_identity_status_schema():
    for name, item in build_catalog_closure_objects().items():
        field_names = {field.name for field in fields(item)}
        assert {"identity", "status", "schema_version"}.issubset(field_names), name
        assert item.schema_version == "0.1", name


def test_l2_phase8_catalog_rejects_inconsistent_counts():
    with pytest.raises(ValueError):
        L2StateCatalog(
            identity=identity(930, L2StateKind.CATALOG),
            status=status(),
            total_object_count=1,
            public_object_count=2,
        )


def test_l2_phase8_validation_summary_rejects_negative_counts():
    with pytest.raises(ValueError):
        L2ValidationSummaryState(identity=identity(931, L2StateKind.CLOSURE), status=status(), failed_count=-1)


def test_l2_phase8_known_issue_rejects_oversized_followup_layer():
    with pytest.raises(ValueError):
        L2KnownIssueState(
            identity=identity(932, L2StateKind.CLOSURE),
            status=status(),
            severity=L2IssueSeverity.INFO,
            target_followup_layer="x" * 65,
        )


def test_l2_phase8_closure_status_keeps_freeze_state_only_semantics():
    assert L2ClosureStatus.READY_FOR_FREEZE.value == "ready_for_freeze"
    assert build_catalog_closure_objects()["freeze"].freeze_status == L2ClosureStatus.READY_FOR_FREEZE
