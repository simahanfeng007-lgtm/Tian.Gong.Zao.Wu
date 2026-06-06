from tiangong_kernel.l5_plugin_host import AffectiveL6HandoffRef, L5L6HandoffFreeze, L5L6HandoffFreezeValidator


def test_affective_l6_handoff_forbids_live_execution():
    handoff = AffectiveL6HandoffRef()
    assert handoff.l6_planning_only_ref
    assert handoff.no_live_execution_ref
    assert handoff.no_tool_call_ref
    assert handoff.no_adapter_call_ref
    assert handoff.no_authorization_ref


def test_final_l5_l6_handoff_includes_affective_refs_and_remains_valid():
    handoff = L5L6HandoffFreeze()
    assert handoff.affective_mount_refs
    assert handoff.affective_modulation_contract_refs
    assert handoff.affective_safety_boundary_refs
    assert handoff.affective_audit_binding_refs
    assert handoff.affective_public_projection_refs
    assert handoff.affective_l6_handoff_refs
    assert L5L6HandoffFreezeValidator().check(handoff)
