import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_goal_priority_and_projection_are_not_execution_plan():
    assert GoalMindState().goal_is_execution_plan is False
    assert GoalProjection().goal_is_execution_plan is False
    assert GoalPriorityScore().is_execution_command is False
    with pytest.raises(ValueError):
        GoalMindState(goal_is_execution_plan=True)
    with pytest.raises(ValueError):
        GoalProjection(goal_is_execution_plan=True)
    with pytest.raises(ValueError):
        GoalPriorityScore(is_execution_command=True)
