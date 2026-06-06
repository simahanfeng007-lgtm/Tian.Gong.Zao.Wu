from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from l2_phase9_builders import build_math_objects
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l2_state import (
    MathConstraintKind,
    MathFeatureKind,
    MathObjectiveKind,
    MathRecommendationState,
)


def test_l2_phase9_math_objects_are_frozen_slots_and_serializable():
    for name, item in build_math_objects().items():
        assert is_dataclass(item), name
        assert hasattr(type(item), "__slots__"), name
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "x"
        assert stable_json_dumps(item), name
        assert len(stable_hash(item)) == 64, name


def test_l2_phase9_math_enums_keep_expected_values():
    assert MathFeatureKind.GOAL_FIT.value == "goal_fit"
    assert MathFeatureKind.AFFECTIVE_BIAS.value == "affective_bias"
    assert MathObjectiveKind.MINIMAL_TOOL_EXPOSURE.value == "minimal_tool_exposure"
    assert MathConstraintKind.L5_REVIEW_REQUIRED.value == "l5_review_required"
    assert MathFeatureKind.UNKNOWN.value == "unknown"


def test_l2_phase9_math_recommendation_is_only_state_not_command():
    recommendation = build_math_objects()["recommendation"]
    assert isinstance(recommendation, MathRecommendationState)
    assert recommendation.required_boundary_refs
    assert recommendation.required_execution_refs
    assert recommendation.recommended_target_ref is not None
    assert not hasattr(recommendation, "run")
    assert not hasattr(recommendation, "apply")
    assert not hasattr(recommendation, "decide")
