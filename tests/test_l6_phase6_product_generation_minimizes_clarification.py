from tiangong_kernel.l6_plugins.product_delivery import *

def test_product_generation_minimizes_clarification():
    suggestion = MinimalQuestionSuggestion()
    hint = ContinueWithoutClarificationHint()
    policy = ProductExecutionFirstPolicy()
    assert suggestion.asks_only_when_blocking is True
    assert hint.safe_to_continue is True
    assert policy.continue_without_clarification_when_safe is True
