import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_no_direct_audit_write():
    assert L6Phase3MindQualityGateDecision(no_direct_audit_write_passed=False).allow_enter_phase4 is False
    declaration = MindPluginDeclaration(plugin_ref="mind:audit_bad", plugin_kind=MindPluginKind.CONTEXT, summary="bad")
    assert declaration.writes_audit is False
    with pytest.raises(ValueError):
        MindPluginDeclaration(plugin_ref="mind:audit_bad", plugin_kind=MindPluginKind.CONTEXT, summary="bad", writes_audit=True)
