from tiangong_kernel.l5_plugin_host import L5L6HandoffFreeze


def test_l5_phase8_l6_handoff_forbids_l3_l4_bypass():
    handoff = L5L6HandoffFreeze()
    refs = set(handoff.l6_forbidden_misuse_refs)
    assert "forbid:l5_handoff_as_l3_l4_call" in refs
    assert "forbid:l1_l4_governance_bypass" in refs
    assert "forbid:direct_tool_or_adapter_call" in refs
    assert handoff.context_belief_world_boundary_refs
    assert handoff.required_context_safety_projection_refs
    assert handoff.required_l6_context_assembler_refs
    assert handoff.no_context_assembly_bypass_ref
    assert handoff.no_tool_output_as_system_instruction_ref
    assert handoff.no_model_output_as_system_instruction_ref
    assert handoff.no_belief_override_event_ref
    assert handoff.no_world_state_without_evidence_ref
    assert handoff.no_memory_injection_without_boundary_review_ref
    assert handoff.skill_tool_release_contract_refs
    assert handoff.self_healing_refs
    assert handoff.self_evolution_requirement_refs
    assert handoff.memory_forgetting_requirement_refs
    assert handoff.resource_budget_boundary_refs
