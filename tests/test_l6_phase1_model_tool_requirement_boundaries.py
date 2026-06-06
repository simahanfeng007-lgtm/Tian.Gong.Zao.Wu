import pytest

from tiangong_kernel.l6_plugins.common import L6ModelCapabilityRequirement, L6ToolCapabilityRequirement, L6ToolSideEffectGrade


def test_model_requirement_is_provider_neutral_and_lowercase_mimo():
    req = L6ModelCapabilityRequirement(
        reasoning=True,
        structured_output=True,
        tool_calling=True,
        provider_neutral_hints=("deepseek_v4", "xiaomi_mimo", "glm_5_1", "minimax_m3", "gpt_5_5"),
    )
    assert req.requirement_only is True
    assert req.provider_selection_allowed is False
    assert req.contains_sdk_import is False
    assert req.raw_http_allowed is False
    assert req.direct_l4_adapter_access is False


def test_model_requirement_rejects_provider_selection_sdk_http_and_bad_mimo_case():
    with pytest.raises(ValueError):
        L6ModelCapabilityRequirement(provider_neutral_hints=("xiaomi_MiMo",))
    with pytest.raises(ValueError):
        L6ModelCapabilityRequirement(provider_selection_allowed=True)
    with pytest.raises(ValueError):
        L6ModelCapabilityRequirement(contains_sdk_import=True)
    with pytest.raises(ValueError):
        L6ModelCapabilityRequirement(raw_http_allowed=True)


def test_tool_requirement_declares_intent_but_holds_no_handle_or_raw_schema():
    req = L6ToolCapabilityRequirement(side_effect_grade=L6ToolSideEffectGrade.READ_ONLY)
    assert req.requirement_only is True
    assert req.stores_tool_handle is False
    assert req.releases_raw_tool_schema is False
    assert req.invokes_tool is False
    assert req.direct_shell_allowed is False
    assert req.direct_file_access_allowed is False
    assert req.direct_network_access_allowed is False


def test_tool_requirement_rejects_direct_actions():
    with pytest.raises(ValueError):
        L6ToolCapabilityRequirement(invokes_tool=True)
    with pytest.raises(ValueError):
        L6ToolCapabilityRequirement(stores_tool_handle=True)
    with pytest.raises(ValueError):
        L6ToolCapabilityRequirement(direct_shell_allowed=True)
