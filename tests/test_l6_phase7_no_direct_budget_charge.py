from tiangong_kernel.l6_plugins.adaptive_collaboration import AdaptivePluginDeclaration, AdaptivePluginKind
import pytest

def test_no_direct_budget_charge():
    with pytest.raises(ValueError):
        AdaptivePluginDeclaration(plugin_ref='decl:l6_phase7_bad', plugin_kind=AdaptivePluginKind.LEARNING_NEED_REVIEW, summary='summary:l6_phase7_bad', charges_budget=True)
