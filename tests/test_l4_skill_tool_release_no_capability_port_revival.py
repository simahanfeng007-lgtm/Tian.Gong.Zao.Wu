from pathlib import Path


def test_l4_skill_tool_release_patch_does_not_revive_legacy_capability_chain():
    files = (
        Path("tiangong_kernel/l4_action_grounding/released_tool_schema_view.py"),
        Path("tiangong_kernel/l4_action_grounding/skill_tool_release_session_context.py"),
        Path("tiangong_kernel/l4_action_grounding/skill_tool_release_chain_index.py"),
    )
    forbidden = (
        "AbilityPackage",
        "AbilityRouter",
        "AbilityExecutor",
        "AbilityPackagePort",
        "CapabilityPort",
        "may_generate_execution_plan",
        "ability_execution_plan",
        "runtime_policy",
        "tiangong_kernel.l5",
        "tiangong_kernel.l6",
    )
    for file in files:
        source = file.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, (file, token)
