from l5_phase5_helpers import validate_all, valid_dependency
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind, has_forbidden_phase5_method


def test_dependency_declaration_has_no_install_or_import_method():
    decl = valid_dependency()
    assert not has_forbidden_phase5_method(decl)


def test_dependency_live_import_locator_is_conflict():
    report = validate_all(dependency_decls=(valid_dependency(dependency_refs=("package.module:function",)),))
    assert any(c.kind is PluginPhase5ConflictKind.DEPENDENCY_LIVE_IMPORT_CONFLICT for c in report.conflicts)
