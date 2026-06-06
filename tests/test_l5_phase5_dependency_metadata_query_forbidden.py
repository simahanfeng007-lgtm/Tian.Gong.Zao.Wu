import types
import tiangong_kernel.l5_plugin_host.phase5_boundary as phase5_boundary


def test_dependency_metadata_live_query_modules_are_not_held_by_phase5_boundary():
    imported_modules = {value.__name__ for value in vars(phase5_boundary).values() if isinstance(value, types.ModuleType)}
    forbidden = ("importlib.metadata", "pkg_resources", "pip._internal", "site")
    assert not any(name in imported_modules for name in forbidden)
