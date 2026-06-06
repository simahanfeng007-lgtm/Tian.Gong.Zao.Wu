import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import AdaptivePluginDeclaration, AdaptivePluginKind

def test_adaptive_plugin_is_not_executor():
    declaration = AdaptivePluginDeclaration(plugin_ref='decl:l6_phase7_learning_need_review', plugin_kind=AdaptivePluginKind.LEARNING_NEED_REVIEW, summary='summary:l6_phase7_learning_need_review')
    assert declaration.is_candidate_only is True
    with pytest.raises(ValueError):
        AdaptivePluginDeclaration(plugin_ref='decl:l6_phase7_bad', plugin_kind=AdaptivePluginKind.LEARNING_NEED_REVIEW, summary='summary:l6_phase7_bad', is_executor=True)
