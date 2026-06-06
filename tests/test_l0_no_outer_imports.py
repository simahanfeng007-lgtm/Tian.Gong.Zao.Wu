import ast
from pathlib import Path

L0_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l0_primitives"
FORBIDDEN_PREFIXES = tuple(f"tiangong_kernel.l{i}" for i in range(1, 7))


def test_l0_does_not_import_outer_layers():
    violations = []
    for path in L0_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(FORBIDDEN_PREFIXES):
                        violations.append((path.name, alias.name))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith(FORBIDDEN_PREFIXES):
                    violations.append((path.name, module))
    assert violations == []
