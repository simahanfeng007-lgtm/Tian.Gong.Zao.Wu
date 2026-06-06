from l3_phase8_builders import build_l3_phase8_objects
from tiangong_kernel.l3_orchestration import (
    OrchestrationIndexKind,
    OrchestrationMathCatalogKind,
    orchestration_stable_json,
)


def test_l3_phase8_component_indexes_cover_all_stages_and_handoffs():
    objects = build_l3_phase8_objects()
    assert objects["component_index"].component_names[-1] == "closure"
    assert objects["module_index"].stable_order is True
    assert objects["stage_index"].stage_names == ("phase1", "phase2", "phase3", "phase4", "phase5", "phase6", "phase7", "phase8")
    assert objects["stage_index"].index_kind is OrchestrationIndexKind.STAGE
    assert "L3ToL6HandoffEnvelope" in objects["handoff_index"].handoff_names
    assert objects["boundary_index"].advisory_only is True


def test_l3_phase8_math_catalog_keeps_advisory_contract():
    objects = build_l3_phase8_objects()
    catalog = objects["math_catalog"]
    assert catalog.catalog_kind is OrchestrationMathCatalogKind.MATH
    assert catalog.advisory_only is True
    assert objects["score_catalog"].score_range_hint == "0.0_to_1.0"
    assert "ranking" in objects["weight_catalog"].allowed_effect_hints
    assert "execute" in objects["math_boundary_note"].forbidden_output_hints
    assert objects["math_report"].consistency_score == 1.0
    assert "l3_math_advisory_contract" in orchestration_stable_json(objects["math_freeze"])
