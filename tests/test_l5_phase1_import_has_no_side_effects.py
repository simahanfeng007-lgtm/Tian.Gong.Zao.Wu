import builtins


def test_importing_l5_plugin_host_exports_only_safe_data_shells(monkeypatch):
    calls = []

    def blocked_file_call(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("file access should not occur during import assertion")

    monkeypatch.setattr(builtins, "open", blocked_file_call)
    import tiangong_kernel.l5_plugin_host as host

    assert calls == []
    assert "PluginManifestView" in host.__all__
    assert "PluginRegistrySnapshot" in host.__all__
    assert "to_l5_json" in host.__all__
