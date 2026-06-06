from l3_phase1_builders import typed
from l3_phase5_builders import build_l3_phase5_objects
from tiangong_kernel.l4_action_grounding import (
    ActionGroundingContext,
    ActionGroundingError,
    ActionGroundingErrorKind,
    ActionGroundingFailure,
    ActionGroundingFailureKind,
    ActionGroundingIdentity,
    ActionGroundingInvariant,
    ActionGroundingInvariantKind,
    ActionGroundingMode,
    ActionGroundingObjectKind,
    ActionGroundingProjection,
    ActionGroundingResult,
    ActionGroundingResultKind,
    ActionGroundingSession,
    ActionGroundingStatus,
    ActionGroundingStatusKind,
    ActionGroundingStep,
    ActionRequestIntake,
    ActionRequestIntakeSummary,
    BoundaryPermitRequiredInvariant,
    DryRunActionGroundingRunner,
    ExecutionDisabledByDefaultFailure,
    FakeActionGroundingRunner,
    NoL4AutonomousExecutionInvariant,
    NoLiveExecutionWithoutL5Invariant,
    NoOpActionGroundingRunner,
)


def build_l4_phase1_objects(include_permit: bool = False):
    phase5 = build_l3_phase5_objects()
    permit_ref = typed(4010, "future_l5_permit_ref") if include_permit else None
    intake = ActionRequestIntake(
        intake_ref=typed(4000, "l4_intake"),
        execution_request=phase5["execution_request"],
        dispatch_request=phase5["dispatch_request"],
        execution_request_ref=phase5["execution_ref"].request_ref,
        execution_plan_ref=phase5["plan_ref"],
        execution_step_refs=(phase5["execution_step"],),
        l5_permit_ref=permit_ref,
    )
    identity = ActionGroundingIdentity(
        action_grounding_ref=typed(4001, "l4_identity"),
        object_kind=ActionGroundingObjectKind.REQUEST_INTAKE,
        source_request_ref=intake.source_request_ref,
    )
    status = ActionGroundingStatus(
        status_ref=typed(4002, "l4_status"),
        status_kind=ActionGroundingStatusKind.INTAKEN,
        mode=ActionGroundingMode.DISABLED_BY_DEFAULT,
        l5_permit_ref=permit_ref,
    )
    context = ActionGroundingContext(
        context_ref=typed(4003, "l4_context"),
        identity_ref=identity.action_grounding_ref,
        intake_ref=intake.intake_ref,
        status_ref=status.status_ref,
        l5_permit_ref=permit_ref,
    )
    step = ActionGroundingStep(
        step_ref=typed(4004, "l4_step"),
        source_l3_step_ref=phase5["execution_step"],
        sequence_index=0,
        l5_permit_ref=permit_ref,
    )
    session = ActionGroundingSession(session_ref=typed(4005, "l4_session"), context_ref=context.context_ref, step_refs=(step.step_ref,))
    error = ActionGroundingError(error_ref=typed(4006, "l4_error"), error_kind=ActionGroundingErrorKind.PERMIT_REQUIRED)
    failure = ActionGroundingFailure(
        failure_ref=typed(4007, "l4_failure"),
        failure_kind=ActionGroundingFailureKind.BOUNDARY_PERMIT_REQUIRED,
        source_request_ref=intake.source_request_ref,
        error=error,
    )
    disabled = ExecutionDisabledByDefaultFailure(failure_ref=typed(4008, "l4_disabled_failure"), source_request_ref=intake.source_request_ref)
    result = ActionGroundingResult(
        result_ref=typed(4009, "l4_result"),
        result_kind=ActionGroundingResultKind.REJECTED,
        source_request_ref=intake.source_request_ref,
        failure=failure,
    )
    projection = ActionGroundingProjection(
        projection_ref=typed(4011, "l4_projection"),
        intake_ref=intake.intake_ref,
        result_ref=result.result_ref,
        failure_ref=failure.failure_ref,
        l3_request_ref=intake.source_request_ref,
        reason_codes=("permit_required",),
    )
    summary = ActionRequestIntakeSummary(summary_ref=typed(4012, "l4_intake_summary"), intake_ref=intake.intake_ref)
    invariant = ActionGroundingInvariant(
        invariant_ref=typed(4013, "l4_invariant"),
        invariant_kind=ActionGroundingInvariantKind.NO_REAL_ACTIONS_IN_PHASE1,
        invariant_name="NoRealActionsInPhase1",
    )
    permit_invariant = BoundaryPermitRequiredInvariant(invariant_ref=typed(4014, "l4_permit_invariant"))
    no_live_invariant = NoLiveExecutionWithoutL5Invariant(invariant_ref=typed(4015, "l4_no_live_invariant"))
    no_auto_invariant = NoL4AutonomousExecutionInvariant(invariant_ref=typed(4016, "l4_no_auto_invariant"))
    fake_runner = FakeActionGroundingRunner(runner_ref=typed(4017, "l4_fake_runner"), l5_permit_ref=permit_ref)
    dry_runner = DryRunActionGroundingRunner(runner_ref=typed(4018, "l4_dry_runner"), l5_permit_ref=permit_ref)
    noop_runner = NoOpActionGroundingRunner(runner_ref=typed(4019, "l4_noop_runner"), l5_permit_ref=permit_ref)
    return locals()
