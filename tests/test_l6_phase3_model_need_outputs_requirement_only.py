import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_model_need_outputs_requirement_only():
    need = MindModelNeed(source_plugin_ref="mind:belief_mind")
    assert need.requirement_only is True
    assert need.calls_model is False
    assert need.requirement.requirement_only is True
    assert need.requirement.direct_l4_adapter_access is False
    with pytest.raises(ValueError):
        MindModelNeed(calls_model=True)
    with pytest.raises(ValueError):
        MindModelNeed(direct_l4_adapter_access=True)
