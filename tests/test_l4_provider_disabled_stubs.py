from tiangong_kernel.l4_action_grounding.model_provider_adapter import build_default_disabled_registry, ModelContextInputEnvelope


def test_l4_all_disabled_stubs_default_reject():
    registry = build_default_disabled_registry()
    expected = {"deepseek_v4", "mimo", "glm_5_1", "minimax_m3", "gpt_5_5"}
    assert set(registry.adapters) == expected
    for adapter in registry.adapters.values():
        failure = adapter.invoke(ModelContextInputEnvelope(context_ref="context-ref:1"))
        assert failure.failure_class == "disabled_by_default"
