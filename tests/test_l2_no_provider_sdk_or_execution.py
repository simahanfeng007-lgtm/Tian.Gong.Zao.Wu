import ast
from pathlib import Path


def test_l2_new_module_has_no_provider_sdk_or_execution():
    path = Path("tiangong_kernel/l2_state/model_interaction_state.py")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    forbidden_roots = {"openai", "anthropic", "dashscope", "zhipuai", "minimax", "deepseek", "requests", "httpx"}
    assert not {name.split('.')[0] for name in names} & forbidden_roots
    assert "urllib.request" not in names
    assert ".post(" not in source and ".get(" not in source
