import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_degradation_suggestion_not_command():
    suggestion = DegradationSuggestion()
    assert suggestion.suggestion_only is True
    assert suggestion.command is False
    assert suggestion.continue_in_degraded_mode is True
    with pytest.raises(ValueError):
        DegradationSuggestion(command=True)
    with pytest.raises(ValueError):
        DegradationSuggestion(aborts_task=True)
