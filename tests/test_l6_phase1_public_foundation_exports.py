from tiangong_kernel.l6_plugins.common import (
    L6PluginManifest,
    L6PluginLifecycleDeclaration,
    L6PluginLifecycleState,
    L6PluginInvocationEnvelope,
    L6PluginOutputEnvelope,
    L6ModelCapabilityRequirement,
    L6ToolCapabilityRequirement,
    L6PermissionRequirement,
    L6BudgetRequirement,
    L6AuditRequirement,
    L6CredentialRequirement,
    L6ContextRequirement,
    L6EventContract,
    L6StateProjectionContract,
    L6PublicProjection,
    L6HandoffContract,
    L6FailureContract,
    L6DegradationContract,
    L6MigrationContract,
    L6RollbackContract,
    L6HotSwitchReadinessContract,
    L6QualityGateDecision,
    L6InvariantRule,
    L6ForbiddenScanRule,
    is_declared_lifecycle_transition_allowed,
    public_projection_from_manifest,
    to_l6_digest,
)


def test_l6_phase1_exports_core_contract_objects():
    manifest = L6PluginManifest(
        plugin_id="l6.phase1.public_foundation",
        plugin_name="L6公共插件底座",
        plugin_version="0.1.0",
        model_capability_requirements=(L6ModelCapabilityRequirement(reasoning=True, provider_neutral_hints=("deepseek_v4", "xiaomi_mimo")),),
        tool_capability_requirements=(L6ToolCapabilityRequirement(),),
        credential_requirements=(L6CredentialRequirement(),),
        event_publications=(L6EventContract(),),
        handoff_contracts=(L6HandoffContract(),),
    )
    assert manifest.source_layer == "L6"
    assert manifest.lifecycle_state is L6PluginLifecycleState.DECLARED
    assert manifest.l5_registry_ref.startswith("l5:")
    projection = public_projection_from_manifest(manifest)
    assert isinstance(projection, L6PublicProjection)
    assert "requirement_only" in projection.status_summary
    assert len(to_l6_digest(manifest)) == 64


def test_l6_lifecycle_is_declarative_and_host_locked():
    declaration = L6PluginLifecycleDeclaration(current_state=L6PluginLifecycleState.ISOLATED)
    assert declaration.terminal_state_host_locked is True
    assert is_declared_lifecycle_transition_allowed("declared", "registered") is True
    assert is_declared_lifecycle_transition_allowed("disabled", "active") is False
