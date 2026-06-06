from tiangong_kernel.l5_plugin_host import PluginHookDeclaration, has_forbidden_phase7_method


def test_hook_declaration_no_handler_or_background_task():
    h = PluginHookDeclaration()
    assert h.no_live_handler_ref
    assert h.no_background_task_ref
    assert not has_forbidden_phase7_method(h)
