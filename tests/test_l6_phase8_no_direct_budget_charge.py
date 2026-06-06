import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosureArtifactBase

def test_no_direct_budget_charge():
    with pytest.raises(ValueError):
        FinalClosureArtifactBase(budget_charged=True)
