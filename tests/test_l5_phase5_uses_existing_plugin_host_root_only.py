from pathlib import Path


def test_existing_plugin_host_root_is_used_without_parallel_src_root():
    assert Path("tiangong_kernel/l5_plugin_host").is_dir()
    assert not Path("src/tiangong/l5/plugin_host").exists()
