def test_l2_phase3_package_and_modules_importable():
    import tiangong_kernel.l2_state as l2_state
    from tiangong_kernel.l2_state import action_effect_state
    from tiangong_kernel.l2_state import model_state
    from tiangong_kernel.l2_state import skill_state
    from tiangong_kernel.l2_state import tool_group_state
    from tiangong_kernel.l2_state import tool_intent_state

    assert skill_state.SkillVisibilityState
    assert tool_group_state.ToolGroupDeclarationState
    assert tool_intent_state.ToolIntentState
    assert model_state.ModelRequestState
    assert action_effect_state.ActionIntentState
    assert l2_state.SkillActivationState
    assert l2_state.ToolGroupReleaseState
    assert l2_state.ModelResponseState
    assert l2_state.EffectObservationState


def test_l2_phase3_public_exports_extend_previous_phase_exports():
    import tiangong_kernel.l2_state as l2_state

    previous_exports = {
        "L2StateIdentity",
        "L2StateStatus",
        "L2StateMetadata",
        "AgentState",
        "RunState",
        "TaskState",
        "GoalPlanState",
        "ContinuityState",
    }
    phase3_exports = {
        "SkillVisibilityStatus",
        "SkillSelectionStatus",
        "SkillActivationStatus",
        "SkillFailureKind",
        "SkillVisibilityState",
        "SkillSelectionState",
        "SkillActivationState",
        "SkillFailureState",
        "ToolGroupDeclarationStatus",
        "ToolGroupVisibilityStatus",
        "ToolGroupReleaseStatus",
        "ToolGroupLeaseStatus",
        "ToolGroupDeclarationState",
        "ToolGroupVisibilityState",
        "ToolGroupReleaseState",
        "ToolGroupLeaseState",
        "ToolIntentSource",
        "ToolIntentStatus",
        "ToolIntentBoundaryStatus",
        "ToolIntentState",
        "ToolIntentBoundaryState",
        "ModelRequestStatus",
        "ModelResponseStatus",
        "ModelFeedbackKind",
        "ModelReflectionStatus",
        "ModelRequestState",
        "ModelResponseState",
        "ModelFeedbackState",
        "ModelReflectionState",
        "ActionIntentSource",
        "ActionIntentStatus",
        "EffectObservationStatus",
        "ActionIntentState",
        "EffectObservationState",
    }
    exports = set(l2_state.__all__)
    assert previous_exports <= exports
    assert phase3_exports <= exports
