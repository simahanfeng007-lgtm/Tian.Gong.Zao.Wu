def test_l2_phase4_package_and_modules_importable():
    import tiangong_kernel.l2_state as l2_state
    from tiangong_kernel.l2_state import boundary_state
    from tiangong_kernel.l2_state import control_state
    from tiangong_kernel.l2_state import environment_state
    from tiangong_kernel.l2_state import resource_state
    from tiangong_kernel.l2_state import risk_decision_state
    from tiangong_kernel.l2_state import security_state

    assert control_state.ControlPlaneState
    assert boundary_state.BoundaryCheckState
    assert risk_decision_state.RiskDecisionState
    assert resource_state.ResourceBudgetState
    assert environment_state.EnvironmentState
    assert security_state.SecurityBoundaryState
    assert l2_state.ControlPlaneState
    assert l2_state.BoundaryBlockedState
    assert l2_state.PolicyReferenceState
    assert l2_state.ResourceLeaseState
    assert l2_state.SandboxState
    assert l2_state.SecretReferenceState


def test_l2_phase4_public_exports_extend_previous_phase_exports():
    import tiangong_kernel.l2_state as l2_state

    previous_exports = {
        "L2StateIdentity",
        "L2StateStatus",
        "L2StateMetadata",
        "AgentState",
        "RunState",
        "TaskState",
        "SkillActivationState",
        "ToolGroupReleaseState",
        "ToolIntentState",
        "ModelFeedbackState",
        "ActionIntentState",
        "EffectObservationState",
    }
    phase4_exports = {
        "ControlPlaneStatus",
        "ControlPlaneMode",
        "ControlSignalStatus",
        "ControlPlaneState",
        "ControlSignalState",
        "ControlConstraintState",
        "BoundaryCheckStatus",
        "BoundaryBlockKind",
        "BoundaryDegradeKind",
        "BoundaryAlternativeKind",
        "BoundaryCheckState",
        "BoundaryBlockedState",
        "BoundaryDegradedState",
        "BoundaryAlternativeState",
        "RiskDecisionStatus",
        "RiskSeverityLabel",
        "PolicyReferenceStatus",
        "RiskDecisionState",
        "PolicyReferenceState",
        "DecisionRecordState",
        "ResourceStatus",
        "ResourceKind",
        "ResourceBudgetState",
        "QuotaState",
        "RateLimitState",
        "ResourceLeaseState",
        "ResourcePressureState",
        "EnvironmentStatus",
        "EnvironmentKind",
        "SandboxStatus",
        "EnvironmentState",
        "SandboxState",
        "ExternalWorldReferenceState",
        "SecurityStatus",
        "PrivacyStatus",
        "CredentialStatus",
        "TrustBoundaryStatus",
        "SecurityBoundaryState",
        "PrivacyCredentialState",
        "TrustBoundaryState",
        "SecretReferenceState",
    }
    exports = set(l2_state.__all__)
    assert previous_exports <= exports
    assert phase4_exports <= exports
