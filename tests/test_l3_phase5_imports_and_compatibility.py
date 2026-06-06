import dataclasses

from l3_phase5_builders import build_l3_phase5_objects
from tiangong_kernel.l3_orchestration import (
    BoundaryCheckRequest,
    BoundaryCheckRequestRef,
    BoundaryExecutionRecommendation,
    BoundaryRouteRanking,
    ExecutionDispatchRequest,
    ExecutionRequest,
    ExecutionRouteRanking,
    IntentRecommendation,
    ModelIntentAdvice,
    SkillDisplayAdvice,
    ToolGroupReleaseAdvice,
)


PHASE5_CLASSES = (
    BoundaryCheckRequestRef,
    BoundaryCheckRequest,
    ExecutionRequest,
    ExecutionDispatchRequest,
    BoundaryRouteRanking,
    ExecutionRouteRanking,
    BoundaryExecutionRecommendation,
)


def test_l3_phase5_objects_import_and_prior_phase_objects_still_import():
    assert SkillDisplayAdvice is not None
    assert ToolGroupReleaseAdvice is not None
    assert ModelIntentAdvice is not None
    assert IntentRecommendation is not None
    objects = build_l3_phase5_objects()
    assert isinstance(objects["boundary_request"], BoundaryCheckRequest)
    assert isinstance(objects["execution_request"], ExecutionRequest)
    assert isinstance(objects["recommendation"], BoundaryExecutionRecommendation)


def test_l3_phase5_public_dataclasses_are_frozen_and_slots():
    for cls in PHASE5_CLASSES:
        assert dataclasses.is_dataclass(cls), cls.__name__
        assert cls.__dataclass_params__.frozen is True, cls.__name__
        assert hasattr(cls, "__slots__"), cls.__name__
