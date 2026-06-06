import pytest
from tiangong_kernel.l5_plugin_host import PluginL6EntryDeclaration, has_forbidden_phase7_method


def test_l6_entry_is_not_plugin_loader():
    e = PluginL6EntryDeclaration()
    assert e.implementation_absent_required
    assert e.no_dynamic_load_ref
    assert not has_forbidden_phase7_method(e)


def test_l6_entry_rejects_dynamic_import_locator():
    with pytest.raises(ValueError):
        PluginL6EntryDeclaration(entry_contract_ref="importlib.import_module:bad")
