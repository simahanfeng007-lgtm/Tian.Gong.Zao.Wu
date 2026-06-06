from tiangong_kernel.l5_plugin_host import PluginLifecycleStateMachine, PluginLifecycleTransitionRule, PluginLifecycleValidator, has_forbidden_method


def test_lifecycle_declaration_classes_have_no_execution_methods():
    assert has_forbidden_method(PluginLifecycleStateMachine) == ()
    assert has_forbidden_method(PluginLifecycleTransitionRule) == ()
    assert "execute" not in PluginLifecycleValidator.__dict__
    assert "apply" not in PluginLifecycleValidator.__dict__
