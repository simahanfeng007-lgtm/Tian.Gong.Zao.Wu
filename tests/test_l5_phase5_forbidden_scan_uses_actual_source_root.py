from pathlib import Path


def test_actual_source_root_contains_phase5_boundary_module():
    assert Path("tiangong_kernel/l5_plugin_host/phase5_boundary.py").is_file()
