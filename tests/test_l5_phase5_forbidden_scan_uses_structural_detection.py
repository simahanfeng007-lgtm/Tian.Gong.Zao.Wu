import types
import tiangong_kernel.l5_plugin_host.phase5_boundary as phase5_boundary


def test_no_forbidden_real_external_modules_held_by_phase5_boundary():
    imported_modules = {value.__name__ for value in vars(phase5_boundary).values() if isinstance(value, types.ModuleType)}
    banned = {"subprocess", "socket", "requests", "httpx", "sqlite3"}
    assert not (imported_modules & banned)
