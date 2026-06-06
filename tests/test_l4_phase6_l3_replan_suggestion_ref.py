import pytest

from l4_phase6_builders import action_ref, phase6_ref, replan_suggestion
from tiangong_kernel.l4_action_grounding import L3ReplanSuggestionRef


def test_l4_phase6_l3_replan_suggestion_ref_does_not_modify_plan():
    suggestion = replan_suggestion()

    assert suggestion.ref_only is True
    assert suggestion.modifies_l3_plan is False
    assert suggestion.creates_plan is False
    assert suggestion.decides_next_step is False


def test_l4_phase6_l3_replan_suggestion_ref_rejects_plan_mutation():
    with pytest.raises(ValueError):
        L3ReplanSuggestionRef(
            replan_suggestion_ref=phase6_ref(160, "l3_replan_suggestion"),
            action_ref=action_ref(),
            modifies_l3_plan=True,
        )
