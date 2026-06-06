import ast
from pathlib import Path


L2_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l2_state"
PHASE3_FILES = {
    "skill_state.py",
    "tool_group_state.py",
    "tool_intent_state.py",
    "model_state.py",
    "action_effect_state.py",
}
FORBIDDEN_FUNCTION_NAMES = {
    "run",
    "execute",
    "invoke",
    "call_model",
    "call_tool",
    "release_tools",
    "select_skill",
    "schedule",
    "restore",
    "load_plugin",
}
FORBIDDEN_TEXT = {
    "ModelPort",
    "ToolExecutor",
    "ModelExecutor",
    "PluginHost",
    "CapabilityPort",
    "AbilityPackagePort",
}


def test_l2_phase3_source_has_no_execution_methods_or_runtime_objects():
    violations = []
    for path in L2_DIR.glob("*.py"):
        if path.name not in PHASE3_FILES:
            continue
        source = path.read_text(encoding="utf-8")
        for text in FORBIDDEN_TEXT:
            if text in source:
                violations.append((path.name, "text", text))
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in FORBIDDEN_FUNCTION_NAMES:
                    violations.append((path.name, "function", node.name))
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in FORBIDDEN_FUNCTION_NAMES:
                    violations.append((path.name, "call", func.id))
                elif isinstance(func, ast.Attribute) and func.attr in FORBIDDEN_FUNCTION_NAMES:
                    violations.append((path.name, "call_attr", func.attr))
    assert violations == []
