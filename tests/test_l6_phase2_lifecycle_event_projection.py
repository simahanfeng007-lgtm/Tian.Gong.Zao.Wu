import pytest

from tiangong_kernel.l6_plugins.common import (
    BeliefCandidateProjection,
    ContextProjection,
    ContextSafetyProjection,
    L6PluginLifecycleContract,
    VersionedPluginEventEnvelope,
    VersionedStateProjectionEnvelope,
    WorldCandidateProjection,
)


def test_lifecycle_contract_states_are_not_authorization_or_permit():
    contract = L6PluginLifecycleContract(lifecycle_state="active_declared")
    assert contract.lifecycle_is_authorization is False
    assert contract.active_is_permit is False
    assert contract.ready_for_orchestration_is_permit is False
    assert contract.registered_with_l5_is_tool_authorization is False
    with pytest.raises(ValueError):
        L6PluginLifecycleContract(active_is_permit=True)
    with pytest.raises(ValueError):
        L6PluginLifecycleContract(ready_for_orchestration_is_permit=True)
    with pytest.raises(ValueError):
        L6PluginLifecycleContract(registered_with_l5_is_tool_authorization=True)


def test_lifecycle_migration_rollback_hotswitch_replay_are_declarations_only():
    assert L6PluginLifecycleContract(lifecycle_state="migration_plan_declared").migration_plan_executes is False
    assert L6PluginLifecycleContract(lifecycle_state="rollback_route_declared").rollback_route_executes is False
    assert L6PluginLifecycleContract(lifecycle_state="hot_switch_readiness_declared").hot_switch_readiness_executes is False
    assert L6PluginLifecycleContract(lifecycle_state="replay_compatibility_declared").replay_compatibility_executes is False
    with pytest.raises(ValueError):
        L6PluginLifecycleContract(migration_plan_executes=True)
    with pytest.raises(ValueError):
        L6PluginLifecycleContract(rollback_route_executes=True)
    with pytest.raises(ValueError):
        L6PluginLifecycleContract(hot_switch_readiness_executes=True)
    with pytest.raises(ValueError):
        L6PluginLifecycleContract(replay_compatibility_executes=True)


def test_lifecycle_isolated_disabled_cannot_self_unblock():
    assert L6PluginLifecycleContract(lifecycle_state="isolated_declared").isolated_or_disabled_host_locked is True
    assert L6PluginLifecycleContract(lifecycle_state="disabled_declared").isolated_or_disabled_host_locked is True
    with pytest.raises(ValueError):
        L6PluginLifecycleContract(lifecycle_state="isolated_declared", plugin_self_unblocks_isolated_disabled=True)


def test_event_envelope_is_not_execution_or_action_replay():
    event = VersionedPluginEventEnvelope()
    assert event.event_is_execution is False
    assert event.event_replay_is_action_replay is False
    assert event.calls_model is False
    assert event.invokes_tool is False
    assert event.writes_state is False
    assert event.direct_plugin_call is False
    with pytest.raises(ValueError):
        VersionedPluginEventEnvelope(calls_model=True)
    with pytest.raises(ValueError):
        VersionedPluginEventEnvelope(invokes_tool=True)
    with pytest.raises(ValueError):
        VersionedPluginEventEnvelope(writes_state=True)
    with pytest.raises(ValueError):
        VersionedPluginEventEnvelope(direct_plugin_call=True)
    with pytest.raises(ValueError):
        VersionedPluginEventEnvelope(action_replay_allowed=True)


def test_event_envelope_payload_is_summary_or_digest_only():
    event = VersionedPluginEventEnvelope(payload_summary_ref="summary:l6_payload", payload_digest="a" * 64)
    assert event.payload_summary_ref == "summary:l6_payload"
    assert event.payload_digest == "a" * 64
    with pytest.raises(ValueError):
        VersionedPluginEventEnvelope(carries_raw_payload=True)
    with pytest.raises(ValueError):
        VersionedPluginEventEnvelope(payload_summary_ref="https://api.example.invalid/raw")


def test_projection_is_candidate_not_l2_fact_and_requires_lifecycle_policies():
    projection = VersionedStateProjectionEnvelope()
    assert projection.projection_is_l2_fact is False
    assert projection.has_expiry_conflict_revocation_rollback is True
    assert projection.candidate_only is True
    assert projection.canonical_fact is False
    assert projection.l2_write_allowed is False
    with pytest.raises(ValueError):
        VersionedStateProjectionEnvelope(candidate_only=False)
    with pytest.raises(ValueError):
        VersionedStateProjectionEnvelope(canonical_fact=True)
    with pytest.raises(ValueError):
        VersionedStateProjectionEnvelope(l2_write_allowed=True)


def test_projection_cannot_write_any_core_state_or_credentials():
    for field_name in (
        "writes_l2_state_fact",
        "mutates_core_state",
        "modifies_memory",
        "modifies_affective_state",
        "modifies_budget",
        "modifies_audit",
        "reads_credential",
    ):
        with pytest.raises(ValueError):
            VersionedStateProjectionEnvelope(**{field_name: True})


def test_context_projection_is_not_prompt_or_context_injection_permit():
    assert ContextProjection().is_prompt is False
    with pytest.raises(ValueError):
        ContextProjection(is_prompt=True)
    with pytest.raises(ValueError):
        ContextProjection(context_injection_permit=True)


def test_belief_candidate_is_not_event_fact_and_world_candidate_is_not_canonical():
    assert BeliefCandidateProjection().event_fact is False
    assert WorldCandidateProjection().canonical_world_state is False
    with pytest.raises(ValueError):
        BeliefCandidateProjection(event_fact=True)
    with pytest.raises(ValueError):
        BeliefCandidateProjection(overwrites_event=True)
    with pytest.raises(ValueError):
        WorldCandidateProjection(canonical_world_state=True)


def test_context_safety_demotes_tool_and_model_outputs():
    safety = ContextSafetyProjection()
    assert safety.tool_output_demoted is True
    assert safety.model_output_demoted is True
    assert safety.instruction_boundary_preserved is True
    with pytest.raises(ValueError):
        ContextSafetyProjection(tool_output_demoted=False)
    with pytest.raises(ValueError):
        ContextSafetyProjection(model_output_demoted=False)
    with pytest.raises(ValueError):
        ContextSafetyProjection(instruction_boundary_preserved=False)
    with pytest.raises(ValueError):
        ContextSafetyProjection(direct_model_context_injection=True)
