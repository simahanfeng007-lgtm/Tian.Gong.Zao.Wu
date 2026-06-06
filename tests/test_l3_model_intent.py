from tiangong_kernel.l3_orchestration.model_invocation_flow import ModelIntent


def test_l3_model_intent_can_list_provider_candidates():
    intent = ModelIntent(intent_ref="intent-ref:1", capability_requirement_ref="req-ref:1", candidate_provider_ids=("deepseek_v4", "mimo"))
    assert intent.llm_remains_main_controller is True
