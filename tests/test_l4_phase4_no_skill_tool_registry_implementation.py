from pathlib import Path


FORBIDDEN_REGISTRY_TERMS = (
    "SkillRegistry",
    "ToolRegistry",
    "ToolGroupRegistry",
    "plugin_host",
    "adapter_registry_runtime",
)


def test_l4_phase4_does_not_implement_skill_tool_registries():
    root = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l4_action_grounding"
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    for term in FORBIDDEN_REGISTRY_TERMS:
        assert term not in source
