from l5_phase5_helpers import validate_all, valid_dependency
from tiangong_kernel.l5_plugin_host import has_live_locator


def test_live_locator_helper_blocks_urls_and_paths():
    assert has_live_locator("https://example.invalid/plugin")
    assert has_live_locator("/tmp/plugin.py")


def test_validator_reports_live_dependency_locator():
    report = validate_all(dependency_decls=(valid_dependency(dependency_refs=("https://example.invalid/pkg",)),))
    assert report.p0_count >= 1
