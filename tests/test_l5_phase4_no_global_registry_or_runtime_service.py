import tiangong_kernel.l5_plugin_host as l5


def test_no_global_runtime_registry_service_exports():
    forbidden = {"RegistryService", "PluginRegistryManager", "PluginLifecycleManager", "PluginRuntimeService", "HostSingleton"}
    assert forbidden.isdisjoint(set(l5.__all__))
    for name in forbidden:
        assert not hasattr(l5, name)
