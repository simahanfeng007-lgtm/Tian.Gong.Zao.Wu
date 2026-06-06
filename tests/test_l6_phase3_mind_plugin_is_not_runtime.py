import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_mind_plugin_group_is_auxiliary_not_runtime():
    group = MindPluginGroupArchitecture()
    assert group.mind_plugin_is_not_runtime is True
    assert len(default_mind_plugin_declarations()) == 13
    for declaration in default_mind_plugin_declarations():
        assert declaration.is_runtime is False
        assert declaration.calls_model is False
        assert declaration.calls_tool is False
    with pytest.raises(ValueError):
        MindPluginGroupArchitecture(creates_parallel_runtime=True)
    with pytest.raises(ValueError):
        MindPluginDeclaration(plugin_ref="mind:bad", plugin_kind=MindPluginKind.CONTEXT, summary="bad", is_runtime=True)
