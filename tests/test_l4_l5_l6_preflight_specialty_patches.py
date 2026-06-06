from dataclasses import fields, replace

from l3_phase1_builders import l2_identity, l2_status, typed
from l4_phase2_builders import audit_requirement, build_gate_input, credential, full_permit, granted_boundary, resource_limit, validate
from l4_phase4_builders import model_request, tool_request
from tiangong_kernel.l1_ports import (
    REQUIRED_EXTERNAL_ADAPTER_PORT_SURFACES,
    BudgetExpansionReviewRequest,
    HandoffEnvelopeSubmitRequest,
    PluginHostReference,
    VersionSwitchIntent,
)
from tiangong_kernel.l2_state import (
    CommunicationEnvelopeState,
    DataGovernanceBindingState,
    L2StateKind,
    MemoryRefState,
    ResourceBoundaryBindingState,
)
from tiangong_kernel.l3_orchestration import (
    ActionBudgetPreflightAdvice,
    AuditChainProjection,
    HandoffContinuityCheckAdvice,
    L3ToL5PluginHostHandoffEnvelope,
    RunOrchestrationPlan,
    VersionMigrationFlowAdvice,
)
from tiangong_kernel.l4_action_grounding import (
    EXTERNAL_SURFACE_CONTRACT_REGISTRY,
    REQUIRED_EXTERNAL_ACTION_SURFACES,
    CommunicationEnvelopeBinding,
    DataGovernanceRefBundle,
    DisabledExternalSurfaceAdapterStub,
    ExternalActionSurface,
    L4ActionAuditChain,
    L4VersionSwitchRequirement,
    SandboxPolicyRef,
)
from tiangong_kernel.l4_execution import (
    L4_L6_SURFACES,
    L5_PLUGIN_HOST_SURFACES,
    L4QualityGateHandoffEnvelope,
    L4RegressionEvidenceIndex,
    L4TestEvidenceIndex,
    L4ToL5AuditChainHandoff,
    L4ToL5PluginHostHandoffEnvelope,
    L4ToL5QualityGateSummary,
    L4ToL5VersionSwitchRequirement,
    L4ToL6MigrationSwitchRequirement,
    L4ToL6ValidationRequirement,
)


def test_audit_chain_gate_is_structural_not_authorization():
    boundary = granted_boundary()
    audit = audit_requirement()
    resource = resource_limit()
    cred = credential()
    permit = full_permit(boundary=boundary, audit=audit, resource=resource, credential=cred)
    base = build_gate_input(
        permit=permit,
        boundary=boundary,
        audit=audit,
        resource=resource,
        credential=cred,
        production_path=True,
    )
    full = replace(
        base,
        event_ref=typed(9001, "event"),
        evidence_ref=typed(9002, "evidence"),
        responsibility_chain_ref=typed(9003, "responsibility_chain"),
        provenance_ref=typed(9004, "provenance"),
    )
    result = validate(full, offset=101)
    assert result.allowed_for_grounding is True
    assert result.validation_result.structurally_accepted_for_grounding is True
    assert result.validation_result.is_authorization is False
    assert result.validation_result.requires_boundary_authorization is True

    missing = validate(base, offset=111)
    assert missing.allowed_for_grounding is False

    chain = L4ActionAuditChain(
        chain_ref=typed(9010, "audit_chain"),
        event_ref=typed(9011, "event"),
        actor_ref=typed(9012, "actor"),
        responsibility_chain_ref=typed(9013, "responsibility"),
        evidence_ref=typed(9014, "evidence"),
        audit_requirement_ref=typed(9015, "audit_requirement"),
        provenance_ref=typed(9016, "provenance"),
    )
    assert chain.has_required_production_refs is True


def test_l5_plugin_host_semantics_are_separate_from_l4_l6_surfaces():
    assert "plugin_host" not in L4_L6_SURFACES
    assert {"subsystem_plugin", "adapter_plugin", "skill_plugin"}.issubset(set(L4_L6_SURFACES))
    assert {"plugin_manifest", "plugin_registry", "plugin_lifecycle", "plugin_isolation"}.issubset(
        set(L5_PLUGIN_HOST_SURFACES)
    )
    envelope = L4ToL5PluginHostHandoffEnvelope(
        handoff_ref=typed(9020, "handoff"),
        package_ref=typed(9021, "package"),
        manifest_material_ref=typed(9022, "manifest_material"),
    )
    assert envelope.handoff_only is True
    assert envelope.implements_plugin_host is False
    assert envelope.dynamically_loads_plugins is False
    assert envelope.writes_plugin_registry is False
    assert PluginHostReference(host_ref=typed(9023, "plugin_host")).host_ref.ref_type == "plugin_host"


def test_external_surfaces_and_sandbox_contract_are_complete_and_ref_only():
    required = set(REQUIRED_EXTERNAL_ACTION_SURFACES)
    assert required == set(REQUIRED_EXTERNAL_ADAPTER_PORT_SURFACES)
    assert {"database", "browser", "git", "build", "test", "sandbox", "storage"}.issubset(required)
    assert ExternalActionSurface.DATABASE.value == "database"
    assert all("disabled_real_stub" in EXTERNAL_SURFACE_CONTRACT_REGISTRY[surface] for surface in required)

    sandbox = SandboxPolicyRef(
        policy_ref=typed(9030, "sandbox_policy"),
        mount_policy_ref=typed(9031, "mount_policy"),
        workdir_policy_ref=typed(9032, "workdir_policy"),
        network_policy_ref=typed(9033, "network_policy"),
        env_policy_ref=typed(9034, "env_policy"),
        process_policy_ref=typed(9035, "process_policy"),
        resource_limit_ref=typed(9036, "resource_limit"),
        credential_policy_ref=typed(9037, "credential_policy"),
        audit_policy_ref=typed(9038, "audit_policy"),
        recovery_policy_ref=typed(9039, "recovery_policy"),
    )
    assert sandbox.has_complete_policy_refs is True
    assert sandbox.creates_real_sandbox is False
    stub = DisabledExternalSurfaceAdapterStub(stub_ref=typed(9040, "stub"), surface="database")
    assert stub.disabled_real_stub is True
    assert stub.executes_external_action is False


def test_quality_gate_and_version_switch_requirements_are_handoff_only():
    quality = L4QualityGateHandoffEnvelope(
        quality_gate_ref=typed(9050, "quality_gate"),
        test_result_refs=(typed(9051, "test_result"),),
        regression_refs=(typed(9052, "regression"),),
    )
    assert quality.report_only is True
    assert quality.approves_l5_l6_start is False
    assert quality.executes_test is False
    assert L4TestEvidenceIndex(index_ref=typed(9053, "test_index")).executes_test is False
    assert L4RegressionEvidenceIndex(baseline_ref=typed(9054, "baseline"), current_ref=typed(9055, "current")).detects_regression is False
    assert L4ToL5QualityGateSummary(handoff_ref=typed(9056, "handoff"), quality_gate_ref=typed(9057, "quality_gate")).l4_approves_permit is False
    assert L4ToL6ValidationRequirement(requirement_ref=typed(9058, "validation_requirement")).implements_validation_system is False

    version = L4VersionSwitchRequirement(requirement_ref=typed(9060, "version_switch_requirement"))
    assert version.executes_hot_switch is False
    assert VersionSwitchIntent(intent_ref=typed(9061, "switch_intent")).intent_ref.ref_type == "switch_intent"
    assert VersionMigrationFlowAdvice(advice_ref=typed(9062, "version_migration_advice")).executes_migration is False
    assert L4ToL5VersionSwitchRequirement(requirement_ref=typed(9063, "l5_switch_requirement")).executes_replay is False
    assert L4ToL6MigrationSwitchRequirement(requirement_ref=typed(9064, "l6_switch_requirement")).executes_migration is False


def test_data_governance_refs_are_available_across_l2_and_l4():
    memory_fields = {item.name for item in fields(MemoryRefState)}
    assert {"privacy_state_refs", "security_state_refs", "consent_ref", "purpose_ref", "retention_policy_ref", "trust_boundary_ref"}.issubset(memory_fields)

    state = DataGovernanceBindingState(
        identity=l2_identity(9070, L2StateKind.MEMORY_CONTEXT),
        status=l2_status(),
        consent_ref=typed(9071, "consent"),
        purpose_ref=typed(9072, "purpose"),
        retention_policy_ref=typed(9073, "retention_policy"),
        trust_boundary_ref=typed(9074, "trust_boundary"),
    )
    assert state.value_absent is True

    bundle = DataGovernanceRefBundle(
        bundle_ref=typed(9075, "data_governance_bundle"),
        privacy_boundary_refs=(typed(9076, "privacy_boundary"),),
        consent_refs=(typed(9077, "consent"),),
        purpose_refs=(typed(9078, "purpose"),),
        retention_policy_refs=(typed(9079, "retention_policy"),),
    )
    assert bundle.has_privacy_governance_refs is True
    assert bundle.contains_plain_secret is False


def test_resource_budget_chain_reaches_l2_l3_l4_model_tool():
    binding = ResourceBoundaryBindingState(
        identity=l2_identity(9080, L2StateKind.RUN),
        status=l2_status(),
        subject_kind="run",
        subject_ref=typed(9081, "run"),
        budget_state_ref=typed(9082, "budget_state"),
    )
    assert binding.consumes_resource is False
    advice = ActionBudgetPreflightAdvice(advice_ref=typed(9083, "budget_advice"), budget_ref=typed(9084, "budget"))
    assert advice.reserves_budget is False

    plan = RunOrchestrationPlan(
        plan_ref=typed(9085, "run_plan"),
        resource_budget_hint_refs=(typed(9086, "budget_hint"),),
        quota_hint_refs=(typed(9087, "quota_hint"),),
        rate_limit_hint_refs=(typed(9088, "rate_limit_hint"),),
        resource_pressure_hint_refs=(typed(9089, "pressure_hint"),),
    )
    assert plan.resource_budget_hint_refs

    model = replace(
        model_request(),
        resource_usage=typed(9090, "resource_usage"),
        resource_budget_ref=typed(9091, "resource_budget"),
        cost_estimate_ref=typed(9092, "cost_estimate"),
    )
    tool = replace(
        tool_request(),
        resource_usage=typed(9093, "resource_usage"),
        resource_budget_ref=typed(9094, "resource_budget"),
        cost_estimate_ref=typed(9095, "cost_estimate"),
    )
    assert model.has_structured_resource_cost_refs is True
    assert tool.has_structured_resource_cost_refs is True
    expansion = BudgetExpansionReviewRequest(
        request_ref=typed(9096, "budget_expansion"),
        requested_extra_budget_ref=typed(9097, "extra_budget"),
        upper_bound_ref=typed(9098, "upper_bound"),
        valid_until_ref=typed(9099, "valid_until"),
        reason_ref=typed(9100, "reason"),
        audit_required_ref=typed(9101, "audit_required"),
    )
    assert expansion.unlimited is False


def test_communication_handoff_chain_is_envelope_first_and_no_authority_escalation():
    request = HandoffEnvelopeSubmitRequest(
        request_ref=typed(9110, "handoff_envelope_request"),
        handoff_ref=typed(9111, "handoff"),
        source_message_envelope_ref=typed(9112, "message_envelope"),
        from_actor_ref=typed(9113, "actor"),
        to_actor_ref=typed(9114, "actor"),
        conversation_ref=typed(9115, "conversation"),
        authority_ref=typed(9116, "authority"),
        provenance_ref=typed(9117, "provenance"),
    )
    assert request.source_message_envelope_ref.ref_type == "message_envelope"
    state = CommunicationEnvelopeState(
        identity=l2_identity(9118, L2StateKind.MEMORY_CONTEXT),
        status=l2_status(),
        message_envelope_ref=typed(9119, "message_envelope"),
    )
    assert state.message_envelope_ref.ref_type == "message_envelope"
    advice = HandoffContinuityCheckAdvice(advice_ref=typed(9120, "handoff_advice"), handoff_ref=typed(9121, "handoff"))
    assert advice.executes_handoff is False
    assert advice.creates_subagent is False
    binding = CommunicationEnvelopeBinding(
        binding_ref=typed(9122, "communication_binding"),
        communication_envelope_ref=typed(9123, "message_envelope"),
        authority_ref=typed(9124, "authority"),
        provenance_ref=typed(9125, "provenance"),
    )
    assert binding.escalates_authority is False


def test_l3_and_l5_audit_plugin_handoff_are_refs_only():
    assert AuditChainProjection(projection_ref=typed(9130, "audit_projection")).writes_audit is False
    assert L3ToL5PluginHostHandoffEnvelope(handoff_ref=typed(9131, "l3_l5_plugin_handoff")).implements_plugin_host is False
    handoff = L4ToL5AuditChainHandoff(handoff_ref=typed(9132, "l4_l5_audit_handoff"))
    assert handoff.handoff_only is True
    assert handoff.writes_audit is False
