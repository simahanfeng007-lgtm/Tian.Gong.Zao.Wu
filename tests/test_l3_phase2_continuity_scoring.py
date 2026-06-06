from dataclasses import replace

from l3_phase2_builders import build_l3_phase2_objects
from tiangong_kernel.l3_orchestration import (
    ContinuityScoreKind,
    ScoreDirection,
    build_recovery_priority_score,
)


def test_l3_phase2_continuity_scores_are_unit_interval_and_explainable():
    objects = build_l3_phase2_objects()
    for key in (
        "continuity_index",
        "resumability_index",
        "severity",
        "readiness",
        "progress",
        "carryover_score",
        "recovery",
        "cancellation",
    ):
        item = objects[key]
        assert 0.0 <= item.value <= 1.0, key
        assert item.advisory_only is True, key
        assert item.reason_items, key


def test_l3_phase2_math_score_vector_reuses_phase1_math骨架():
    vector = build_l3_phase2_objects()["math_score_vector"]
    names = {name for name, _value, _direction in vector.score_entries}
    assert ContinuityScoreKind.CONTINUITY_INDEX.value in names
    assert ContinuityScoreKind.STEP_READINESS.value in names
    assert any(direction is ScoreDirection.COST for _name, _value, direction in vector.score_entries)
    assert 0.0 <= vector.normalized_score <= 1.0


def test_l3_phase2_affective_weight_only_changes_priority_score_not_execution():
    objects = build_l3_phase2_objects()
    affective = objects["continuity_set"].affective_input
    dynamic = objects["continuity_set"].dynamic_drive_input
    lower_affective = replace(affective, persistence_weight=0.0)
    lower_dynamic = replace(dynamic, priority_weight=0.0)
    base = objects["recovery"]
    changed = build_recovery_priority_score(objects["severity"], objects["resumability_index"], lower_dynamic, lower_affective)
    assert changed.value < base.value
    assert changed.advisory_only is True
    assert not hasattr(changed, "execution_token")
    assert not hasattr(changed, "permission_grant")
