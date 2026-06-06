import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_learning_evolution_not_apply_migration_rollback_or_switch():
    state = LearningEvolutionMindState()
    assert state.applies_migration is False
    assert state.applies_rollback is False
    assert state.performs_switch is False
    with pytest.raises(ValueError):
        LearningEvolutionMindState(applies_migration=True)
    with pytest.raises(ValueError):
        MigrationSuggestion(applies_migration=True)
    with pytest.raises(ValueError):
        HotSwitchReadinessHint(performs_switch=True)
