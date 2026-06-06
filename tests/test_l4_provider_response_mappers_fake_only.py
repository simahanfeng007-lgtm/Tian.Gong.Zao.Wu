from tiangong_kernel.l4_action_grounding.model_provider_adapter import GLM51ResponseMapper


def test_l4_response_mapper_uses_fake_ref_only():
    out = GLM51ResponseMapper().map_response("response-ref:test")
    assert out.normalized_only is True
    assert out.output_ref == "response-ref:test"
