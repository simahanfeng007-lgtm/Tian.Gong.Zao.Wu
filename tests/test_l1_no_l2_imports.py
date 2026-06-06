import ast
from pathlib import Path

L1_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l1_ports"
FORBIDDEN_PREFIXES = tuple(f"tiangong_kernel.l{i}" for i in range(2, 7))


def test_l1_does_not_import_l2_to_l6():
    violations = []
    for path in L1_DIR.glob("*.py"):
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
