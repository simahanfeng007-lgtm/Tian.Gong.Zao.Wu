from l3_phase7_builders import build_l3_phase7_objects
from tiangong_kernel.l3_orchestration import (
    CandidateChangeRef,
    EvolutionFlowRequest,
    ExperimentFlowRequest,
    IterationFlowRequest,
    RecoveryRequest,
    SelfLearningFlowEntryAdvice,
    ValidationRequest,
)


def test_l3_phase7_objects_import_and_build():
    objects = build_l3_phase7_objects()
    assert isinstance(objects["validation_request"], ValidationRequest)
    assert isinstance(objects["recovery_request"], RecoveryRequest)
    assert isinstance(objects["experiment_request"], ExperimentFlowRequest)
    assert isinstance(objects["iteration_request"], IterationFlowRequest)
    assert isinstance(objects["evolution_request"], EvolutionFlowRequest)
    assert isinstance(objects["self_learning"], SelfLearningFlowEntryAdvice)
    assert isinstance(objects["change_ref"], CandidateChangeRef)
    assert objects["phase6"] is not None


def test_l3_phase7_keeps_prior_phase_objects_available():
    objects = build_l3_phase7_objects()
    assert objects["phase6"]["subsystem_request"].request_only is True
    assert objects["phase6"]["phase5"]["execution_request"].request_only is True
    assert objects["phase6"]["phase5"]["phase4"]["tool_advice"].advisory_only is True
