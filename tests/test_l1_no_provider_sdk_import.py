import ast
from pathlib import Path


def _imports(path: str) -> set[str]:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_l1_new_module_has_no_provider_sdk_import():
    names = _imports("tiangong_kernel/l1_ports/model_provider_governance_ports.py")
    forbidden_roots = {"openai", "anthropic", "dashscope", "zhipuai", "minimax", "deepseek"}
    assert not {name.split('.')[0] for name in names} & forbidden_roots
    assert not any(name.startswith("google.genai") for name in names)
