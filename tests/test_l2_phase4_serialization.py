from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l2_state import (
    BoundaryAlternativeKind,
    BoundaryAlternativeState,
    BoundaryBlockKind,
    BoundaryBlockedState,
    BoundaryCheckState,
    BoundaryCheckStatus,
    BoundaryDegradeKind,
    BoundaryDegradedState,
    ControlConstraintState,
    ControlPlaneMode,
    ControlPlaneState,
    ControlPlaneStatus,
    ControlSignalState,
    ControlSignalStatus,
    CredentialStatus,
    DecisionRecordState,
    EnvironmentKind,
    EnvironmentState,
    EnvironmentStatus,
    ExternalWorldReferenceState,
    L2StateIdentity,
    L2StateKind,
    L2StateStatus,
    L2StateStatusKind,
    PolicyReferenceState,
    PolicyReferenceStatus,
    PrivacyCredentialState,
    PrivacyStatus,
    QuotaState,
    RateLimitState,
    ResourceBudgetState,
    ResourceKind,
    ResourceLeaseState,
    ResourcePressureState,
    ResourceStatus,
    RiskDecisionState,
    RiskDecisionStatus,
    RiskSeverityLabel,
    SandboxState,
    SandboxStatus,
    SecretReferenceState,
    SecurityBoundaryState,
    SecurityStatus,
    TrustBoundaryState,
    TrustBoundaryStatus,
)
from tests.test_l2_phase3_serialization import build_phase3_chain


def ref(prefix: str, index: int) -> RefId:
    return RefId(f"{prefix}:{index:032x}")


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(ref("phase4", index), ref_type)


def identity(index: int, kind: L2StateKind = L2StateKind.BOUNDARY) -> L2StateIdentity:
    return L2StateIdentity(state_ref=typed(index, kind.value), kind=kind)


def status() -> L2StateStatus:
    return L2StateStatus(kind=L2StateStatusKind.DECLARED, reason="phase4 fixture")


def build_phase4_objects():
    phase3 = build_phase3_chain()
    run_ref = phase3["run"].identity.state_ref
    task_ref = phase3["task"].identity.state_ref
    skill_state_ref = phase3["skill_activation"].identity.state_ref
    tool_group_release_ref = phase3["tool_release"].identity.state_ref
    tool_intent_ref = phase3["tool_intent"].identity.state_ref
    action_intent_ref = phase3["action_intent"].identity.state_ref
    effect_observation_ref = phase3["effect_observation"].identity.state_ref
    model_feedback_ref = phase3["feedback"].identity.state_ref

    policy = PolicyReferenceState(
        identity=identity(100),
        status=status(),
        reference_status=PolicyReferenceStatus.MATCHED,
        policy_ref=typed(101, "policy"),
        policy_name="a5-boundary-policy",
        policy_version_ref=typed(102, "policy_version"),
        applies_to_refs=(tool_intent_ref,),
        source_boundary_ref=typed(103, "boundary"),
        evidence_refs=(typed(104, "evidence"),),
        summary="short policy label only",
    )
    boundary_check = BoundaryCheckState(
        identity=identity(110),
        status=status(),
        check_status=BoundaryCheckStatus.PASSED,
        checked_subject_ref=tool_intent_ref,
        boundary_ref=typed(111, "boundary"),
        risk_view_ref=typed(112, "risk_view"),
        decision_ref=typed(113, "decision"),
        policy_state_refs=(policy.identity.state_ref,),
        evidence_refs=(typed(114, "evidence"),),
        audit_refs=(typed(115, "audit"),),
        reason_code="external_passed",
        summary="external boundary result",
    )
    blocked = BoundaryBlockedState(
        identity=identity(120),
        status=status(),
        block_kind=BoundaryBlockKind.RISK_BLOCK,
        boundary_check_ref=boundary_check.identity.state_ref,
        blocked_subject_ref=action_intent_ref,
        blocking_policy_refs=(policy.identity.state_ref,),
        recoverable=True,
        requires_upper_layer_action=True,
    )
    degraded = BoundaryDegradedState(
        identity=identity(121),
        status=status(),
        degrade_kind=BoundaryDegradeKind.READ_ONLY,
        boundary_check_ref=boundary_check.identity.state_ref,
        original_subject_ref=tool_intent_ref,
        degraded_subject_ref=typed(122, "tool_intent"),
        allowed_scope_refs=(typed(123, "scope"),),
        restricted_scope_refs=(typed(124, "scope"),),
    )
    alternative = BoundaryAlternativeState(
        identity=identity(125),
        status=status(),
        alternative_kind=BoundaryAlternativeKind.SUMMARY_ALTERNATIVE,
        boundary_check_ref=boundary_check.identity.state_ref,
        alternative_subject_ref=typed(126, "tool_intent"),
        alternative_skill_ref=typed(127, "skill"),
        alternative_tool_group_ref=typed(128, "tool_group"),
        requires_confirmation=True,
    )
    risk = RiskDecisionState(
        identity=identity(130),
        status=status(),
        decision_status=RiskDecisionStatus.DECISION_OBSERVED,
        severity_label=RiskSeverityLabel.A5,
        subject_ref=action_intent_ref,
        risk_view_ref=typed(131, "risk_view"),
        decision_ref=typed(132, "decision"),
        policy_state_refs=(policy.identity.state_ref,),
        boundary_check_ref=boundary_check.identity.state_ref,
        score_snapshot_ref=typed(133, "score_snapshot"),
    )
    decision = DecisionRecordState(
        identity=identity(134),
        status=status(),
        recorded_status=RiskDecisionStatus.DENY_RECORDED,
        decision_ref=risk.decision_ref,
        decision_source_ref=typed(135, "decision_source"),
        subject_ref=tool_intent_ref,
        expires_at_ref=typed(136, "time"),
    )
    budget = ResourceBudgetState(
        identity=identity(140),
        status=status(),
        resource_status=ResourceStatus.LIMITED,
        resource_kind=ResourceKind.TOKEN_BUDGET,
        budget_ref=typed(141, "budget"),
        subject_ref=run_ref,
        limit_snapshot="limit:1000",
        used_snapshot="used:200",
        remaining_snapshot="remaining:800",
    )
    quota = QuotaState(
        identity=identity(142),
        status=status(),
        resource_status=ResourceStatus.AVAILABLE,
        quota_ref=typed(143, "quota"),
        resource_kind=ResourceKind.TOOL_CALL_BUDGET,
        subject_ref=task_ref,
        window_ref=typed(144, "time_window"),
        limit_snapshot="limit:10",
        used_snapshot="used:1",
    )
    rate_limit = RateLimitState(
        identity=identity(145),
        status=status(),
        resource_status=ResourceStatus.RATE_LIMITED,
        resource_kind=ResourceKind.MODEL_CALL_BUDGET,
        quota_ref=quota.quota_ref,
        retry_after_ref=typed(146, "time"),
        rate_limit_reason="external_rate_limit",
        applies_to_refs=(run_ref, task_ref),
    )
    lease = ResourceLeaseState(
        identity=identity(147),
        status=status(),
        resource_status=ResourceStatus.RESERVED_RECORDED,
        resource_kind=ResourceKind.TOOL_LEASE,
        lease_ref=typed(148, "lease"),
        subject_ref=tool_group_release_ref,
        tool_group_release_state_ref=tool_group_release_ref,
        granted_scope_refs=(typed(149, "scope"),),
        expires_at_ref=typed(150, "time"),
    )
    pressure = ResourcePressureState(
        identity=identity(151),
        status=status(),
        resource_status=ResourceStatus.LIMITED,
        pressure_level="medium",
        resource_state_refs=(budget.identity.state_ref, rate_limit.identity.state_ref),
        affected_subject_refs=(run_ref, task_ref),
        suggested_boundary_refs=(boundary_check.identity.state_ref,),
    )
    sandbox = SandboxState(
        identity=identity(160),
        status=status(),
        sandbox_status=SandboxStatus.LIMITED_RECORDED,
        sandbox_ref=typed(161, "sandbox"),
        subject_ref=run_ref,
        allowed_scope_refs=(typed(162, "scope"),),
        restricted_scope_refs=(typed(163, "scope"),),
        trust_boundary_ref=typed(164, "trust_boundary"),
    )
    environment = EnvironmentState(
        identity=identity(165),
        status=status(),
        environment_status=EnvironmentStatus.AVAILABLE_RECORDED,
        environment_kind=EnvironmentKind.SANDBOX,
        environment_ref=typed(166, "environment"),
        subject_ref=run_ref,
        sandbox_state_ref=sandbox.identity.state_ref,
        boundary_state_refs=(boundary_check.identity.state_ref,),
        resource_state_refs=(budget.identity.state_ref,),
    )
    external = ExternalWorldReferenceState(
        identity=identity(167),
        status=status(),
        access_status=EnvironmentStatus.LIMITED_RECORDED,
        external_ref=typed(168, "external_world"),
        environment_ref=environment.environment_ref,
        trust_boundary_ref=sandbox.trust_boundary_ref,
        privacy_ref=typed(169, "privacy"),
    )
    privacy = PrivacyCredentialState(
        identity=identity(170),
        status=status(),
        privacy_status=PrivacyStatus.SENSITIVE_DATA_REF_ONLY,
        credential_status=CredentialStatus.REF_ONLY,
        privacy_ref=typed(171, "privacy"),
        credential_ref=typed(172, "credential"),
        secret_ref=typed(173, "secret"),
        subject_ref=tool_intent_ref,
        boundary_check_refs=(boundary_check.identity.state_ref,),
    )
    secret = SecretReferenceState(
        identity=identity(174),
        status=status(),
        credential_status=CredentialStatus.REF_ONLY,
        secret_ref=privacy.secret_ref,
        credential_ref=privacy.credential_ref,
        owner_ref=typed(175, "actor"),
        scope_refs=(typed(176, "scope"),),
    )
    trust = TrustBoundaryState(
        identity=identity(177),
        status=status(),
        trust_boundary_status=TrustBoundaryStatus.CROSSING_RECORDED,
        trust_boundary_ref=sandbox.trust_boundary_ref,
        inside_refs=(run_ref,),
        outside_refs=(external.external_ref,),
        crossing_subject_ref=tool_intent_ref,
        boundary_check_ref=boundary_check.identity.state_ref,
        risk_decision_state_ref=risk.identity.state_ref,
    )
    security = SecurityBoundaryState(
        identity=identity(178),
        status=status(),
        security_status=SecurityStatus.WARNING_RECORDED,
        security_boundary_ref=typed(179, "security_boundary"),
        subject_ref=effect_observation_ref,
        trust_boundary_ref=trust.trust_boundary_ref,
        privacy_state_refs=(privacy.identity.state_ref,),
        credential_state_refs=(secret.identity.state_ref,),
        boundary_check_refs=(boundary_check.identity.state_ref,),
        risk_decision_state_refs=(risk.identity.state_ref,),
    )
    control = ControlPlaneState(
        identity=identity(180),
        status=status(),
        control_status=ControlPlaneStatus.ACTIVE,
        mode=ControlPlaneMode.STRICT,
        run_ref=run_ref,
        task_ref=task_ref,
        skill_state_ref=skill_state_ref,
        tool_intent_state_ref=tool_intent_ref,
        action_intent_state_ref=action_intent_ref,
        model_feedback_state_ref=model_feedback_ref,
        boundary_state_refs=(boundary_check.identity.state_ref,),
        risk_decision_state_refs=(risk.identity.state_ref,),
        resource_state_refs=(budget.identity.state_ref,),
        security_state_refs=(security.identity.state_ref,),
        policy_state_refs=(policy.identity.state_ref,),
    )
    signal = ControlSignalState(
        identity=identity(181),
        status=status(),
        signal_status=ControlSignalStatus.PENDING,
        signal_ref=typed(182, "control_signal"),
        control_plane_state_ref=control.identity.state_ref,
        run_ref=run_ref,
        task_ref=task_ref,
        source_ref=typed(183, "control_plane"),
        target_refs=(tool_intent_ref,),
        boundary_state_refs=(boundary_check.identity.state_ref,),
    )
    constraint = ControlConstraintState(
        identity=identity(184),
        status=status(),
        control_plane_state_ref=control.identity.state_ref,
        constraint_refs=(typed(185, "constraint"),),
        applies_to_refs=(tool_intent_ref, action_intent_ref),
        boundary_state_refs=(boundary_check.identity.state_ref,),
        trust_boundary_refs=(trust.trust_boundary_ref,),
    )
    return {
        "policy": policy,
        "boundary_check": boundary_check,
        "blocked": blocked,
        "degraded": degraded,
        "alternative": alternative,
        "risk": risk,
        "decision": decision,
        "budget": budget,
        "quota": quota,
        "rate_limit": rate_limit,
        "lease": lease,
        "pressure": pressure,
        "sandbox": sandbox,
        "environment": environment,
        "external": external,
        "privacy": privacy,
        "secret": secret,
        "trust": trust,
        "security": security,
        "control": control,
        "signal": signal,
        "constraint": constraint,
        "phase3": phase3,
    }


def test_l2_phase4_objects_are_stably_serializable_and_hashable():
    for name, item in build_phase4_objects().items():
        if name == "phase3":
            continue
        first = stable_json_dumps(item)
        second = stable_json_dumps(item)
        digest = stable_hash(item)
        assert first == second
        assert '"schema_version":"0.1"' in first
        assert len(digest) == 64


def test_l2_phase4_serialization_contains_only_references_for_sensitive_state():
    payload = stable_json_dumps(build_phase4_objects()["privacy"])
    assert '"redacted":true' in payload
    assert '"value_absent":true' in payload
    assert "sk-" not in payload
    assert "bearer" not in payload.lower()
