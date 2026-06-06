from tiangong_kernel.l5_plugin_host import PluginLifecycleTransitionRule


def test_transition_rule_class_has_no_apply_or_transition_methods():
    for name in ("apply", "transition_to", "next_state", "commit", "execute", "run", "start", "stop", "mount", "enable", "disable", "rollback", "hot_switch", "migrate", "replay"):
        assert name not in PluginLifecycleTransitionRule.__dict__
