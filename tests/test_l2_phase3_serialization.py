from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l2_state import (
    ActionIntentSource,
    ActionIntentState,
    ActionIntentStatus,
    EffectObservationState,
    EffectObservationStatus,
    L2StateIdentity,
    L2StateKind,
    L2StateStatus,
    L2StateStatusKind,
    ModelFeedbackKind,
    ModelFeedbackState,
    ModelReflectionState,
    ModelReflectionStatus,
    ModelRequestState,
    ModelRequestStatus,
    ModelResponseState,
    ModelResponseStatus,
    RunState,
    SkillActivationState,
    SkillActivationStatus,
    SkillFailureKind,
    SkillFailureState,
    SkillSelectionState,
    SkillSelectionStatus,
    SkillVisibilityState,
    SkillVisibilityStatus,
    TaskState,
    ToolGroupDeclarationState,
    ToolGroupDeclarationStatus,
    ToolGroupLeaseState,
    ToolGroupLeaseStatus,
    ToolGroupReleaseState,
    ToolGroupReleaseStatus,
    ToolGroupVisibilityState,
    ToolGroupVisibilityStatus,
    ToolIntentBoundaryState,
    ToolIntentBoundaryStatus,
    ToolIntentSource,
    ToolIntentState,
    ToolIntentStatus,
)


def ref(prefix: str, index: int) -> RefId:
    return RefId(f"{prefix}:{index:032x}")


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(ref("ref", index), ref_type)


def identity(index: int, kind: L2StateKind) -> L2StateIdentity:
    return L2StateIdentity(state_ref=typed(index, kind.value), kind=kind)


def status() -> L2StateStatus:
    return L2StateStatus(kind=L2StateStatusKind.DECLARED, reason="phase3 fixture")


def build_phase3_chain():
    run = RunState(identity=identity(1, L2StateKind.RUN), status=status())
    task = TaskState(identity=identity(2, L2StateKind.TASK), status=status(), run_ref=run.identity.state_ref)
    skill_ref = typed(3, "skill")
    tool_group_ref = typed(4, "tool_group")
    tool_ref = typed(5, "tool")
    message_ref = typed(6, "message")
    model_ref = typed(7, "model")
    observation_ref = typed(8, "observation")
    effect_ref = typed(9, "effect")
    evidence_ref = typed(10, "evidence")
    metric_ref = typed(11, "metric")
    target_ref = typed(12, "target")
    context_ref = typed(13, "context_snapshot")
    audit_ref = typed(14, "audit")

    skill_visibility = SkillVisibilityState(
        identity=identity(20, L2StateKind.SKILL),
        status=status(),
        visibility_status=SkillVisibilityStatus.VISIBLE,
        skill_ref=skill_ref,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
        visible_tool_group_refs=(tool_group_ref,),
        audit_refs=(audit_ref,),
    )
    skill_selection = SkillSelectionState(
        identity=identity(21, L2StateKind.SKILL),
        status=status(),
        selection_status=SkillSelectionStatus.SELECTED,
        skill_ref=skill_ref,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
        selected_by_ref=model_ref,
        source_message_ref=message_ref,
    )
    skill_activation = SkillActivationState(
        identity=identity(22, L2StateKind.SKILL),
        status=status(),
        activation_status=SkillActivationStatus.WAITING_TOOL_GROUP,
        skill_ref=skill_ref,
        selection_state_ref=skill_selection.identity.state_ref,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
        tool_group_state_refs=(tool_group_ref,),
    )
    skill_failure = SkillFailureState(
        identity=identity(23, L2StateKind.SKILL),
        status=status(),
        failure_kind=SkillFailureKind.TOOL_GROUP_MISSING,
        skill_ref=skill_ref,
        activation_state_ref=skill_activation.identity.state_ref,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
        evidence_refs=(evidence_ref,),
    )
    tool_declaration = ToolGroupDeclarationState(
        identity=identity(30, L2StateKind.TOOL_GROUP),
        status=status(),
        declaration_status=ToolGroupDeclarationStatus.DECLARED,
        tool_group_ref=tool_group_ref,
        skill_ref=skill_ref,
        skill_activation_ref=skill_activation.identity.state_ref,
        required_tool_refs=(tool_ref,),
    )
    tool_visibility = ToolGroupVisibilityState(
        identity=identity(31, L2StateKind.TOOL_GROUP),
        status=status(),
        visibility_status=ToolGroupVisibilityStatus.VISIBLE,
        tool_group_ref=tool_group_ref,
        declaration_state_ref=tool_declaration.identity.state_ref,
        skill_ref=skill_ref,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
        visible_tool_refs=(tool_ref,),
    )
    tool_release = ToolGroupReleaseState(
        identity=identity(32, L2StateKind.TOOL_GROUP),
        status=status(),
        release_status=ToolGroupReleaseStatus.RELEASED,
        tool_group_ref=tool_group_ref,
        visibility_state_ref=tool_visibility.identity.state_ref,
        skill_ref=skill_ref,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
        released_tool_refs=(tool_ref,),
    )
    tool_lease = ToolGroupLeaseState(
        identity=identity(33, L2StateKind.TOOL_GROUP),
        status=status(),
        lease_status=ToolGroupLeaseStatus.LEASED,
        tool_group_ref=tool_group_ref,
        release_state_ref=tool_release.identity.state_ref,
        lease_ref=typed(34, "lease"),
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
    )
    model_request = ModelRequestState(
        identity=identity(40, L2StateKind.MODEL),
        status=status(),
        request_status=ModelRequestStatus.VISIBLE_CONTEXT_BUILT,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
        model_ref=model_ref,
        visible_skill_refs=(skill_ref,),
        visible_tool_group_refs=(tool_group_ref,),
        context_snapshot_ref=context_ref,
        input_message_refs=(message_ref,),
    )
    model_response = ModelResponseState(
        identity=identity(41, L2StateKind.MODEL),
        status=status(),
        response_status=ModelResponseStatus.TOOL_INTENT_FOUND,
        request_state_ref=model_request.identity.state_ref,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
        model_ref=model_ref,
        output_message_ref=typed(42, "message"),
    )
    tool_intent = ToolIntentState(
        identity=identity(50, L2StateKind.TOOL_INTENT),
        status=status(),
        intent_status=ToolIntentStatus.PARSED,
        intent_source=ToolIntentSource.MODEL,
        tool_ref=tool_ref,
        tool_group_ref=tool_group_ref,
        tool_group_release_ref=tool_release.identity.state_ref,
        skill_ref=skill_ref,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
        model_response_ref=model_response.identity.state_ref,
        source_message_ref=model_response.output_message_ref,
        argument_digest="sha256:phase3",
    )
    tool_boundary = ToolIntentBoundaryState(
        identity=identity(51, L2StateKind.TOOL_INTENT),
        status=status(),
        boundary_status=ToolIntentBoundaryStatus.WAITING_CHECK,
        tool_intent_ref=tool_intent.identity.state_ref,
        tool_ref=tool_ref,
        tool_group_ref=tool_group_ref,
        skill_ref=skill_ref,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
    )
    action_intent = ActionIntentState(
        identity=identity(60, L2StateKind.TOOL_INTENT),
        status=status(),
        action_status=ActionIntentStatus.READY_FOR_UPPER_LAYER,
        action_source=ActionIntentSource.MODEL_TOOL_INTENT,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
        skill_ref=skill_ref,
        tool_intent_ref=tool_intent.identity.state_ref,
        tool_ref=tool_ref,
        target_ref=target_ref,
        boundary_state_ref=tool_boundary.identity.state_ref,
    )
    effect_observation = EffectObservationState(
        identity=identity(61, L2StateKind.OBSERVATION),
        status=status(),
        observation_status=EffectObservationStatus.OBSERVATION_PENDING,
        action_intent_ref=action_intent.identity.state_ref,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
        observation_refs=(observation_ref,),
        effect_refs=(effect_ref,),
        metric_refs=(metric_ref,),
        evidence_refs=(evidence_ref,),
    )
    feedback = ModelFeedbackState(
        identity=identity(70, L2StateKind.MODEL),
        status=status(),
        feedback_kind=ModelFeedbackKind.TASK_PROGRESS,
        response_state_ref=model_response.identity.state_ref,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
        skill_ref=skill_ref,
        tool_group_ref=tool_group_ref,
        tool_intent_ref=tool_intent.identity.state_ref,
        observation_refs=(observation_ref,),
        evidence_refs=(evidence_ref,),
    )
    reflection = ModelReflectionState(
        identity=identity(71, L2StateKind.MODEL),
        status=status(),
        reflection_status=ModelReflectionStatus.RECORDED,
        response_state_ref=model_response.identity.state_ref,
        feedback_state_ref=feedback.identity.state_ref,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
        source_message_ref=model_response.output_message_ref,
        related_skill_refs=(skill_ref,),
        related_tool_refs=(tool_ref,),
    )
    return {
        "run": run,
        "task": task,
        "skill_visibility": skill_visibility,
        "skill_selection": skill_selection,
        "skill_activation": skill_activation,
        "skill_failure": skill_failure,
        "tool_declaration": tool_declaration,
        "tool_visibility": tool_visibility,
        "tool_release": tool_release,
        "tool_lease": tool_lease,
        "model_request": model_request,
        "model_response": model_response,
        "tool_intent": tool_intent,
        "tool_boundary": tool_boundary,
        "action_intent": action_intent,
        "effect_observation": effect_observation,
        "feedback": feedback,
        "reflection": reflection,
    }


def test_l2_phase3_objects_are_stably_serializable_and_hashable():
    for item in build_phase3_chain().values():
        first = stable_json_dumps(item)
        second = stable_json_dumps(item)
        digest = stable_hash(item)
        assert first == second
        assert '"schema_version":"0.1"' in first
        assert len(digest) == 64
