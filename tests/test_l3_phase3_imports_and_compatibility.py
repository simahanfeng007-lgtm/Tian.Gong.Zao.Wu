from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from l3_phase1_builders import build_l3_objects
from l3_phase2_builders import build_l3_phase2_objects
from l3_phase3_builders import build_l3_phase3_objects
from tiangong_kernel import l3_orchestration as l3


REQUIRED_EXPORTS = {
    "SkillVisibilityRequestRef",
    "SkillDisplayAdvice",
    "SkillSelectionAdvice",
    "SkillActivationAdvice",
    "ToolGroupResolveRequestRef",
    "ToolGroupReleaseAdvice",
    "ToolGroupLeaseAdvice",
    "SkillMatchScore",
    "ToolGroupMinimalityScore",
    "ToolExposureCostScore",
    "SkillToolRouteRanking",
    "SkillToolMathInput",
    "SkillToolMathResult",
    "SkillToolRecommendation",
    "SkillToolStateTransitionSuggestion",
}


def test_l3_phase3_public_exports_are_available():
    for name in REQUIRED_EXPORTS:
        assert hasattr(l3, name), name
        assert name in l3.__all__, name


def test_l3_phase1_and_phase2_builders_still_work():
    assert build_l3_objects()["recommendation"].advisory_only is True
    assert build_l3_phase2_objects()["continuity_set"].advisory_only is True


def test_l3_phase3_objects_are_frozen_slots_dataclasses():
    for name, item in build_l3_phase3_objects().items():
        assert is_dataclass(item), name
        assert item.__dataclass_params__.frozen is True, name
        assert hasattr(type(item), "__slots__"), name
        if hasattr(item, "schema_version"):
            with pytest.raises(FrozenInstanceError):
                item.schema_version = "x"
