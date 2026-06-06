import pytest

from tiangong_kernel.l6_plugins.common import (
    L3PluginCandidateView,
    L6MiniSpecialtyDesignEnvelope,
    L6PluginAdmissionDecision,
    L6PluginAdmissionKind,
    L6PluginDiscoverableProjection,
    L6PluginInvocationRequest,
    L6PluginOutputReturnEnvelope,
    L6PluginOutputStatus,
    L6PublicContractPatchProposal,
)


def test_discoverable_projection_is_not_invocable_or_callable():
    projection = L6PluginDiscoverableProjection()
    assert projection.discoverable_is_invocable is False
    with pytest.raises(ValueError):
        L6PluginDiscoverableProjection(callable_ref="ref:l6_callable")
    with pytest.raises(ValueError):
        L6PluginDiscoverableProjection(contains_endpoint=True)
    with pytest.raises(ValueError):
        L6PluginDiscoverableProjection(contains_secret=True)
    with pytest.raises(ValueError):
        L6PluginDiscoverableProjection(discoverable_is_invocable=True)


def test_l3_candidate_view_cannot_import_or_call_l6_plugin():
    view = L3PluginCandidateView()
    assert view.public_projection_readonly is True
    with pytest.raises(ValueError):
        L3PluginCandidateView(imports_l6_plugin=True)
    with pytest.raises(ValueError):
        L3PluginCandidateView(calls_l6_plugin=True)
    with pytest.raises(ValueError):
        L3PluginCandidateView(public_projection_readonly=False)


def test_invocation_request_requires_l3_l5_envelope_and_no_direct_access():
    request = L6PluginInvocationRequest()
    assert request.caller_layer == "L3_ORCHESTRATION"
    assert request.discoverable_is_invocable is False
    assert request.active_is_authorized is False
    with pytest.raises(ValueError):
        L6PluginInvocationRequest(caller_layer="L6_DIRECT")
    for field_name in ("imports_plugin", "calls_plugin_directly", "bypasses_l5_host", "invokes_model", "invokes_tool", "writes_l2_state_fact"):
        with pytest.raises(ValueError):
            L6PluginInvocationRequest(**{field_name: True})


def test_output_return_envelope_requirements_are_not_execution_or_l4_call():
    output = L6PluginOutputReturnEnvelope(status=L6PluginOutputStatus.NEEDS_MODEL, model_capability_requirement_refs=("model-cap:l6_need",))
    assert output.output_requirement_is_execution is False
    assert output.model_capability_requirement_refs == ("model-cap:l6_need",)
    for field_name in ("calls_model", "invokes_tool", "calls_l4_adapter", "writes_l2_state_fact", "decrements_budget", "writes_audit_record", "suggestion_is_command"):
        with pytest.raises(ValueError):
            L6PluginOutputReturnEnvelope(**{field_name: True})


def test_ordinary_plugin_admission_sop_passes_with_required_refs():
    decision = L6PluginAdmissionDecision(admission_kind=L6PluginAdmissionKind.ORDINARY_PLUGIN)
    assert decision.allowed_for_general_plugin_sop is True
    assert decision.authorizes_execution is False
    assert decision.bypasses_l5 is False


def test_new_type_plugin_requires_mini_specialty_design():
    with pytest.raises(ValueError):
        L6PluginAdmissionDecision(admission_kind=L6PluginAdmissionKind.NEW_TYPE_PLUGIN)
    decision = L6PluginAdmissionDecision(
        admission_kind=L6PluginAdmissionKind.NEW_TYPE_PLUGIN,
        mini_specialty_design_ref="ref:l6_mini_specialty_design",
    )
    assert decision.allowed_for_general_plugin_sop is True
    assert L6MiniSpecialtyDesignEnvelope().changes_public_contract is False


def test_public_contract_breaking_plugin_is_blocked_from_direct_admission():
    with pytest.raises(ValueError):
        L6PluginAdmissionDecision(admission_kind=L6PluginAdmissionKind.PUBLIC_CONTRACT_BREAKING_PLUGIN)
    with pytest.raises(ValueError):
        L6PluginAdmissionDecision(
            admission_kind=L6PluginAdmissionKind.PUBLIC_CONTRACT_BREAKING_PLUGIN,
            contract_patch_proposal_ref="ref:l6_patch_proposal",
            approved_declared=True,
        )
    decision = L6PluginAdmissionDecision(
        admission_kind=L6PluginAdmissionKind.PUBLIC_CONTRACT_BREAKING_PLUGIN,
        contract_patch_proposal_ref="ref:l6_patch_proposal",
        approved_declared=False,
    )
    assert decision.allowed_for_general_plugin_sop is False
    assert L6PublicContractPatchProposal().applies_patch is False


def test_admission_p0_p1_blocks_approval_declaration():
    assert L6PluginAdmissionDecision(p0_count=1).approved_declared is False
    assert L6PluginAdmissionDecision(p1_count=1).approved_declared is False
