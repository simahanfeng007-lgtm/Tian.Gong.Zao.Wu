import dataclasses

from l3_phase4_builders import build_l3_phase4_objects
from tiangong_kernel.l3_orchestration import (
    ActionIntentAdvice,
    ActionIntentEnvelope,
    ActionIntentRef,
    IntentRecommendation,
    IntentRouteRanking,
    ModelIntentAdvice,
    ModelIntentEnvelope,
    ModelIntentRef,
    SkillDisplayAdvice,
    ToolGroupReleaseAdvice,
    ToolIntentAdvice,
    ToolIntentEnvelope,
    ToolIntentRef,
)


PHASE4_CLASSES = (
    ModelIntentRef,
    ToolIntentRef,
    ActionIntentRef,
    ModelIntentEnvelope,
    ToolIntentEnvelope,
    ActionIntentEnvelope,
    ModelIntentAdvice,
    ToolIntentAdvice,
    ActionIntentAdvice,
    IntentRouteRanking,
    IntentRecommendation,
)


def test_l3_phase4_objects_import_and_prior_phase_objects_still_import():
    assert SkillDisplayAdvice is not None
    assert ToolGroupReleaseAdvice is not None
    objects = build_l3_phase4_objects()
    assert isinstance(objects["model_advice"], ModelIntentAdvice)
    assert isinstance(objects["tool_advice"], ToolIntentAdvice)
    assert isinstance(objects["action_advice"], ActionIntentAdvice)


def test_l3_phase4_public_dataclasses_are_frozen_and_slots():
    for cls in PHASE4_CLASSES:
        assert dataclasses.is_dataclass(cls), cls.__name__
        assert cls.__dataclass_params__.frozen is True, cls.__name__
        assert hasattr(cls, "__slots__"), cls.__name__
