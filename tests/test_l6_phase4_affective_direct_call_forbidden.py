import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_affective_direct_call_forbidden():
    declarations = default_cognitive_continuity_plugin_declarations()
    affective = [item for item in declarations if item.plugin_kind == CognitiveContinuityPluginKind.AFFECTIVE_REENTRY][0]
    assert affective.direct_plugin_link is False
    assert affective.dispatches_model is False
    assert affective.dispatches_tool is False
    with pytest.raises(ValueError):
        CognitiveContinuityPluginDeclaration(
            plugin_ref="l6_phase4:bad_affective",
            plugin_kind=CognitiveContinuityPluginKind.AFFECTIVE_REENTRY,
            summary="summary:l6_phase4_bad",
            direct_plugin_link=True,
        )
