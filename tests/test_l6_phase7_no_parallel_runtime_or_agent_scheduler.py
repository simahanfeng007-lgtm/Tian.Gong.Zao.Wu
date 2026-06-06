from tiangong_kernel.l6_plugins.adaptive_collaboration import AdaptivePluginDeclaration, AdaptivePluginKind
import pytest

def test_no_parallel_runtime_or_agent_scheduler():
    with pytest.raises(ValueError):
        AdaptivePluginDeclaration(plugin_ref='decl:l6_phase7_bad', plugin_kind=AdaptivePluginKind.LEARNING_NEED_REVIEW, summary='summary:l6_phase7_bad', creates_parallel_runtime=True)
    with pytest.raises(ValueError):
        AdaptivePluginDeclaration(plugin_ref='decl:l6_phase7_bad2', plugin_kind=AdaptivePluginKind.LEARNING_NEED_REVIEW, summary='summary:l6_phase7_bad2', creates_agent_scheduler=True)
