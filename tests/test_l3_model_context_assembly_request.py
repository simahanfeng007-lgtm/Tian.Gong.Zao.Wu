from tiangong_kernel.l3_orchestration.model_invocation_flow import ModelContextAssemblyRequest


def test_l3_context_assembly_is_request_only():
    req = ModelContextAssemblyRequest(context_request_ref="ctx-req:1", capability_requirement_ref="req-ref:1", max_context_tokens_hint=1000)
    assert req.assembled_context_ref_expected is True
