from l3_phase8_builders import build_l3_phase8_objects
from tiangong_kernel.l3_orchestration import OrchestrationProjectionKind, orchestration_stable_hash


def test_l3_phase8_projection_is_serializable_and_does_not_write_l2():
    objects = build_l3_phase8_objects()
    projection = objects["projection"]
    assert projection.projection_only is True
    assert projection.no_l2_write is True
    assert projection.summary_projection.run_ref == objects["phase7"]["run_ref"]
    assert projection.math_projection.advisory_only is True
    assert projection.audit_ref_projection.no_audit_write is True
    assert projection.state_update_suggestions[0].no_persistence is True
    assert objects["projection_envelope"].projection_only is True
    assert objects["projection_report"].consistency_score == 1.0
    assert orchestration_stable_hash(projection) == orchestration_stable_hash(projection)


def test_l3_phase8_projection_kinds_are_data_only():
    objects = build_l3_phase8_objects()
    assert objects["projection_ref"].projection_kind is OrchestrationProjectionKind.SUMMARY
    assert objects["math_projection"].projection_ref.projection_kind is OrchestrationProjectionKind.MATH
    assert objects["route_projection"].top_route_ref == objects["phase7"]["validation_ranking"].top_route_ref
