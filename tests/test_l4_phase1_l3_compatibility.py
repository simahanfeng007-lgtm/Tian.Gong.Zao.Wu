from l4_phase1_builders import build_l4_phase1_objects
from tiangong_kernel.l3_orchestration import ExecutionDispatchRequest, ExecutionPlanRef, ExecutionRequest, ExecutionStepRef
from tiangong_kernel.l4_action_grounding import ActionRequestIntake


def test_l4_phase1_intake_carries_l3_execution_request_and_dispatch_request():
    objects = build_l4_phase1_objects()
    intake = objects["intake"]
    assert isinstance(intake, ActionRequestIntake)
    assert isinstance(intake.execution_request, ExecutionRequest)
    assert isinstance(intake.dispatch_request, ExecutionDispatchRequest)
    assert intake.execution_request.request_only is True
    assert intake.dispatch_request.request_only is True
    assert intake.source_request_ref == intake.execution_request_ref


def test_l4_phase1_intake_carries_l3_plan_and_step_refs():
    objects = build_l4_phase1_objects()
    intake = objects["intake"]
    assert isinstance(intake.execution_plan_ref, ExecutionPlanRef)
    assert all(isinstance(item, ExecutionStepRef) for item in intake.execution_step_refs)
    assert intake.has_l5_permit_ref is False


def test_l4_phase1_with_future_l5_ref_still_only_marks_ref_presence():
    objects = build_l4_phase1_objects(include_permit=True)
    intake = objects["intake"]
    assert intake.has_l5_permit_ref is True
    assert intake.intake_only is True
    assert objects["context"].live_action_enabled is False
