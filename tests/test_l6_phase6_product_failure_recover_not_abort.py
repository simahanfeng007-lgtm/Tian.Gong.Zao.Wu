import pytest
from tiangong_kernel.l6_plugins.product_delivery import *

def test_product_failure_recover_not_abort():
    recovery = ProductionRecoverySuggestion()
    degraded = ProductionDegradedContinuationSuggestion()
    assert recovery.aborts_by_default is False
    assert degraded.stops_task is False
    with pytest.raises(ValueError):
        ProductionRecoverySuggestion(aborts_by_default=True)
