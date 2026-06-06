import pytest
from tiangong_kernel.l6_plugins.product_delivery import *

def test_product_dispatch_intent_not_execution():
    intent = ProductExecutionDispatchIntent()
    assert intent.executes_now is False
    with pytest.raises(ValueError):
        ProductExecutionDispatchIntent(executes_now=True)
