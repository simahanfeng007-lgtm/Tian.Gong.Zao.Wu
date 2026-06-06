import ast
from pathlib import Path


def test_l3_new_module_has_no_provider_sdk_import():
    tree = ast.parse(Path("tiangong_kernel/l3_orchestration/model_invocation_flow.py").read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    forbidden_roots = {"openai", "anthropic", "dashscope", "zhipuai", "minimax", "deepseek"}
    assert not {name.split('.')[0] for name in names} & forbidden_roots
    assert not any(name.startswith("google.genai") for name in names)
