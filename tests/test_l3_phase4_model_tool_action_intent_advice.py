from l3_phase4_builders import build_l3_phase4_objects
from tiangong_kernel.l3_orchestration import (
    ActionIntentAdvice,
    ModelIntentAdvice,
    ToolIntentAdvice,
)


def test_model_intent_advice_is_structural_and_advisory():
    objects = build_l3_phase4_objects()
    advice = objects["model_advice"]
    assert isinstance(advice, ModelIntentAdvice)
    assert advice.advisory_only is True
    assert advice.completeness_score.value == 0.75
    assert objects["model_clarification"].question_hints
    assert not hasattr(advice, "model_client")


def test_tool_intent_advice_tracks_missing_parameters_without_tool_call():
    objects = build_l3_phase4_objects()
    advice = objects["tool_advice"]
    assert isinstance(advice, ToolIntentAdvice)
    assert advice.advisory_only is True
    assert objects["tool_parameter_score"].missing_parameter_names == ("target_path",)
    assert objects["missing_parameter_advice"].priority > 0.0
    assert not hasattr(advice, "tool_executor")
    assert not hasattr(advice, "tool_call_args")


def test_action_intent_advice_is_not_action_execution():
    objects = build_l3_phase4_objects()
    advice = objects["action_advice"]
    assert isinstance(advice, ActionIntentAdvice)
    assert advice.advisory_only is True
    assert objects["action_readiness"].value > 0.0
    assert objects["reversibility_hint"].reversibility_score == 0.76
    assert not hasattr(advice, "executor")
    assert not hasattr(advice, "dispatch_token")
