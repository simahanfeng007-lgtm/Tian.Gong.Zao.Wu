import types
import tiangong_kernel.l5_plugin_host.phase5_boundary as phase5_boundary


def test_phase5_module_does_not_hold_l4_module_objects():
    imported_modules = {value.__name__ for value in vars(phase5_boundary).values() if isinstance(value, types.ModuleType)}
    assert not any(name.startswith("tiangong_kernel.l4_") for name in imported_modules)
