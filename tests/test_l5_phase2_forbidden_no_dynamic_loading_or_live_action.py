import tiangong_kernel.l5_plugin_host as host


def test_exports_do_not_expose_loading_or_live_action_surfaces():
    blocked_fragments = ("Loader", "Runner", "Executor", "Sandbox", "RegistryWriter", "ActionAdapter")
    for exported in host.__all__:
        assert not any(fragment in exported for fragment in blocked_fragments)
    assert "Ability" "Package" not in host.__all__
    assert "Capability" "Port" not in host.__all__
    assert "Ability" "Package" "Port" not in host.__all__
