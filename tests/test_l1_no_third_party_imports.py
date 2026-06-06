import ast
import sys
from pathlib import Path

L1_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l1_ports"
LOCAL_ROOTS = {"tiangong_kernel"}
ALLOWED_NON_STDLIB = {"__future__"}
STDLIB = set(getattr(sys, "stdlib_module_names", ())) | set(sys.builtin_module_names) | ALLOWED_NON_STDLIB


def _root_name(name: str) -> str:
    return name.split(".", 1)[0]


def test_l1_uses_only_stdlib_l0_and_l1_imports():
    violations = []
    for path in L1_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = _root_name(alias.name)
                    if root not in STDLIB and root not in LOCAL_ROOTS:
                        violations.append((path.name, alias.name))
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    continue
                module = node.module or ""
                root = _root_name(module)
                if root not in STDLIB and root not in LOCAL_ROOTS:
                    violations.append((path.name, module))
    assert violations == []
