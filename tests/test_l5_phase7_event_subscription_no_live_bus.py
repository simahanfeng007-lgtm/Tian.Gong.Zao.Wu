from tiangong_kernel.l5_plugin_host import PluginEventSubscriptionDeclaration, has_forbidden_phase7_method


def test_event_subscription_no_live_bus_or_emit():
    s = PluginEventSubscriptionDeclaration()
    assert s.no_live_subscription_ref
    assert s.no_event_emit_ref
    assert not has_forbidden_phase7_method(s)
