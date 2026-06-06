from tiangong_kernel.l2_state import (
    BoundaryAlternativeKind,
    BoundaryDegradeKind,
)
from tests.test_l2_phase4_serialization import build_phase4_objects


def test_l2_phase4_boundary_degraded_records_original_degraded_and_scopes():
    objects = build_phase4_objects()
    degraded = objects["degraded"]

    assert degraded.degrade_kind is BoundaryDegradeKind.READ_ONLY
    assert degraded.boundary_check_ref == objects["boundary_check"].identity.state_ref
    assert degraded.original_subject_ref == objects["phase3"]["tool_intent"].identity.state_ref
    assert degraded.degraded_subject_ref is not None
    assert degraded.allowed_scope_refs
    assert degraded.restricted_scope_refs


def test_l2_phase4_boundary_alternative_records_path_without_selection():
    objects = build_phase4_objects()
    alternative = objects["alternative"]

    assert alternative.alternative_kind is BoundaryAlternativeKind.SUMMARY_ALTERNATIVE
    assert alternative.boundary_check_ref == objects["boundary_check"].identity.state_ref
    assert alternative.alternative_skill_ref is not None
    assert alternative.alternative_tool_group_ref is not None
    assert alternative.requires_confirmation is True
    assert not hasattr(alternative, "select")
    assert not hasattr(alternative, "route")
