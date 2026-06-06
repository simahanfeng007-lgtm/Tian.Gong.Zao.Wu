from l4_phase1_builders import build_l4_phase1_objects
from l4_phase3_builders import envelope, phase3_ref
from tiangong_kernel.l4_action_grounding import (
    ActionGroundingContext,
    ActionGroundingFailure,
    ActionGroundingProjection,
    ActionGroundingResult,
    ActionGroundingResultKind,
    ActionGroundingSession,
    ActionGroundingStep,
    AdapterMode,
    NoOpActionAdapter,
)


def test_l4_phase3_adapter_refs_wire_into_phase1_context_session_step_result_failure_projection():
    phase1 = build_l4_phase1_objects()
    adapter = NoOpActionAdapter()
    output = adapter.invoke(envelope(mode=AdapterMode.NO_OP))

    context = ActionGroundingContext(
        context_ref=phase3_ref(90, "l4_context"),
        identity_ref=phase1["identity"].action_grounding_ref,
        intake_ref=phase1["intake"].intake_ref,
        adapter_descriptor_refs=(adapter.adapter_descriptor.identity.adapter_ref,),
        adapter_registry_ref=phase3_ref(91, "adapter_registry"),
        adapter_selection_ref=phase3_ref(92, "adapter_selection"),
    )
    step = ActionGroundingStep(
        step_ref=phase3_ref(93, "l4_step"),
        adapter_descriptor_ref=adapter.adapter_descriptor.identity.adapter_ref,
        adapter_selection_result_ref=phase3_ref(94, "adapter_selection_result"),
    )
    session = ActionGroundingSession(
        session_ref=phase3_ref(95, "l4_session"),
        context_ref=context.context_ref,
        step_refs=(step.step_ref,),
        adapter_output_refs=(output.output_ref,),
    )
    result = ActionGroundingResult(
        result_ref=phase3_ref(96, "l4_result"),
        result_kind=ActionGroundingResultKind.NO_OP,
        adapter_output_ref=output.output_ref,
        adapter_selection_result_ref=phase3_ref(94, "adapter_selection_result"),
        adapter_mode_hint="no_op",
    )
    failure = ActionGroundingFailure(
        failure_ref=phase3_ref(97, "l4_failure"),
        adapter_failure_ref=phase3_ref(98, "adapter_failure"),
        adapter_selection_result_ref=phase3_ref(94, "adapter_selection_result"),
    )
    projection = ActionGroundingProjection(
        projection_ref=phase3_ref(99, "l4_projection"),
        intake_ref=phase1["intake"].intake_ref,
        result_ref=result.result_ref,
        failure_ref=failure.failure_ref,
        adapter_projection_ref=phase3_ref(100, "adapter_projection"),
        adapter_registry_projection_ref=phase3_ref(101, "adapter_registry_projection"),
    )

    assert context.live_action_enabled is False
    assert session.adapter_output_refs == (output.output_ref,)
    assert result.real_action_performed is False
    assert failure.live_action_performed is False
    assert projection.adapter_projection_ref is not None
