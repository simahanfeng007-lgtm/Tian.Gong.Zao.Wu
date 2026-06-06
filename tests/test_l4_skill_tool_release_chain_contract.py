from pathlib import Path

from tiangong_kernel.l4_action_grounding import SkillToolReleaseChainIndex


def test_l4_skill_tool_release_chain_contract_docs_and_index_cover_full_path():
    contract = Path("docs/skill_direct_tool_release_chain_contract_zh.txt").read_text(encoding="utf-8")
    matrix = Path("docs/skill_tool_release_trace_matrix_zh.csv").read_text(encoding="utf-8")
    required_terms = (
        "SkillProjection/Exposure",
        "SkillRequest/Selection",
        "SkillAuthorization/L5ReviewHint",
        "ToolGroupRelease",
        "ReleasedToolSchemaView",
        "ToolCallEnvelope",
        "ToolActionResult/ToolResultEnvelope",
        "ModelContinuation/L3ReplanSuggestion",
        "L2 StateUpdateSuggestion",
    )
    for term in required_terms:
        assert term in contract
    assert "tool_schema_refs" in matrix
    assert "l2_state_update_suggestion_ref" in matrix

    index = SkillToolReleaseChainIndex()
    assert index.index_only is True
    assert index.reference_only is True
    assert index.no_action is True
    assert "released_tool_schema_view" in index.chain_steps
    assert "ToolResultReturnContext" in index.l4_object_names
