import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosureArtifactBase

def test_no_old_runtime_abilitypackage_backflow():
    with pytest.raises(ValueError):
        FinalClosureArtifactBase(old_runtime_backflow=True)
