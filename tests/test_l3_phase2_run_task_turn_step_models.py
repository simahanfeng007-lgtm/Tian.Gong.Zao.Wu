from dataclasses import FrozenInstanceError, is_dataclass
import importlib

import pytest

from l3_phase2_builders import build_l3_phase2_objects


def test_l3_phase2_package_exports_core_surface():
    module = importlib.import_module("tiangong_kernel.l3_orchestration")
    required = {
        "RunOrchestrationRef",
        "RunOrchestrationStateView",
        "RunOrchestrationPlan",
        "RunProgressSnapshot",
        "RunContinuityEvaluation",
        "RunResumeAdvice",
        "TaskOrchestrationRef",
        "TaskOrchestrationPlan",
        "TaskProgressSnapshot",
        "TaskContinuityEvaluation",
        "TaskResumeAdvice",
        "TaskInterruptionAdvice",
        "TurnOrchestrationRef",
        "TurnOrchestrationPlan",
        "TurnSequenceRef",
        "TurnCarryoverHint",
        "TurnContinuityEvaluation",
        "StepSequence",
        "StepTransitionCandidate",
        "StepTransitionAdvice",
        "StepReadinessEvaluation",
        "StepProgressSnapshot",
        "StepResumeAdvice",
    }
    assert required.issubset(set(module.__all__))
    for name in required:
        assert hasattr(module, name), name


def test_l3_phase2_submodules_import_cleanly():
    submodules = (
        "orchestration_lifecycle",
        "orchestration_progress",
        "orchestration_step_sequence",
        "orchestration_turn",
        "orchestration_continuity",
        "orchestration_transition_advice",
        "orchestration_resume",
        "orchestration_run",
        "orchestration_task",
    )
    for name in submodules:
        importlib.import_module(f"tiangong_kernel.l3_orchestration.{name}")


def test_l3_phase2_objects_are_frozen_slots_dataclasses():
    for name, item in build_l3_phase2_objects().items():
        assert is_dataclass(item), name
        assert item.__dataclass_params__.frozen is True, name
        assert hasattr(type(item), "__slots__"), name
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "x"
