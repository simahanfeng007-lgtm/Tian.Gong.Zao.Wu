from tiangong_kernel.l4_action_grounding.model_provider_adapter import GPT55LiveAdapterSkeleton, ModelContextInputEnvelope


def test_l4_live_skeleton_rejects_without_l5_permit():
    failure = GPT55LiveAdapterSkeleton().invoke(ModelContextInputEnvelope(context_ref="context-ref:1"))
    assert failure.failure_code == "l5_permit_required"
