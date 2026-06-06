from l4_phase4_builders import adapter_input, l3_binding, phase4_ref, tool_arguments


def test_l4_phase4_l3_intent_binding_only_builds_structural_requests():
    binding = l3_binding()
    model_request = binding.to_model_action_request(
        request_ref=phase4_ref(60, "model_action_request"),
        model_target_ref=phase4_ref(61, "model_target"),
        prompt_or_message_ref=phase4_ref(62, "prompt_or_message"),
        input_envelope=adapter_input("model_action"),
    )
    tool_request = binding.to_tool_action_request(
        request_ref=phase4_ref(63, "tool_action_request"),
        tool_ref=phase4_ref(6, "tool"),
        tool_group_ref=phase4_ref(5, "tool_group"),
        arguments_envelope=tool_arguments(),
    )
    assert binding.structural_only is True
    assert binding.mutates_l3 is False
    assert binding.l4_generates_intent is False
    assert binding.resolves_skill_or_tool is False
    assert model_request.l3_model_intent_ref == binding.model_intent_ref.intent_ref
    assert tool_request.l3_tool_intent_ref == binding.tool_intent_ref.intent_ref
    assert tool_request.tool_group_context.registers_tool is False
