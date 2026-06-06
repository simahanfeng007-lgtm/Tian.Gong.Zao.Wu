import dataclasses

from l3_phase6_builders import build_l3_phase6_objects
from tiangong_kernel.l3_orchestration import (
    AffectiveServiceRequest,
    BoundaryCheckRequest,
    CandidateProposalAdvice,
    ContextCarryoverAdvice,
    ExecutionRequest,
    LearningServiceRequest,
    MemoryServiceRequest,
    ModelIntentAdvice,
    ObservationFeedbackAdvice,
    ObservationResultRef,
    RetrievalServiceRequest,
    SkillDisplayAdvice,
    SubsystemServiceRequest,
    ToolGroupReleaseAdvice,
)


PHASE6_CLASSES = (
    ObservationResultRef,
    ObservationFeedbackAdvice,
    ContextCarryoverAdvice,
    SubsystemServiceRequest,
    MemoryServiceRequest,
    RetrievalServiceRequest,
    LearningServiceRequest,
    AffectiveServiceRequest,
    CandidateProposalAdvice,
)


def test_l3_phase6_objects_import_and_prior_phase_objects_still_import():
    assert SkillDisplayAdvice is not None
    assert ToolGroupReleaseAdvice is not None
    assert ModelIntentAdvice is not None
    assert BoundaryCheckRequest is not None
    assert ExecutionRequest is not None
    objects = build_l3_phase6_objects()
    assert isinstance(objects["observation_ref"], ObservationResultRef)
    assert isinstance(objects["memory_request"], MemoryServiceRequest)
    assert isinstance(objects["subsystem_request"], SubsystemServiceRequest)


def test_l3_phase6_public_dataclasses_are_frozen_and_slots():
    for cls in PHASE6_CLASSES:
        assert dataclasses.is_dataclass(cls), cls.__name__
        assert cls.__dataclass_params__.frozen is True, cls.__name__
        assert hasattr(cls, "__slots__"), cls.__name__
