from __future__ import annotations

from tiangong_kernel.l4_action_grounding.math_model_adapter import ExternalModelAdapter


def test_math_model_adapter_respects_a5_like_boundary() -> None:
    descriptor = ExternalModelAdapter().adapter_descriptor

    assert descriptor.requires_l5_permit is True
    assert descriptor.calls_external_service is False
    assert descriptor.accesses_network is False
    assert descriptor.executes_shell is False
    assert descriptor.writes_l2_state is False
    assert descriptor.decides_strategy is False
    assert descriptor.turns_score_into_action is False
    assert descriptor.implements_l6_plugin is False
