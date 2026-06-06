from tiangong_kernel.l4_action_grounding.model_provider_adapter import MiMoToolCallMapper


def test_l4_tool_call_mapper_normalizes_shape():
    call = MiMoToolCallMapper().normalize_tool_call({"id":"tc1", "name":"demo", "arguments_ref":"args-ref:1"})
    assert call["raw_arguments_not_embedded"] is True
    assert call["name"] == "demo"
