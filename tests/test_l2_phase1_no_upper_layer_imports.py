import ast
import sys
from pathlib import Path


L2_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l2_state"
LOCAL_ROOTS = {"tiangong_kernel"}
ALLOWED_NON_STDLIB = {"__future__"}
STDLIB = set(getattr(sys, "stdlib_module_names", ())) | set(sys.builtin_module_names) | ALLOWED_NON_STDLIB
FORBIDDEN_LOCAL_PREFIXES = (
    "tiangong_kernel.l3_",
    "tiangong_kernel.l4_",
    "tiangong_kernel.l5_",
    "tiangong_kernel.l6_",
    "tiangong_kernel.runtime",
    "tiangong_kernel.ability",
    "tiangong_kernel.capability",
)


def _root_name(name: str) -> str:
    return name.split(".", 1)[0]


def test_l2_phase1_uses_only_stdlib_l0_l1_and_local_l2_imports():
    violations = []
    for path in L2_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = _root_name(alias.name)
                    if root not in STDLIB and root not in LOCAL_ROOTS:
                        violations.append((path.name, alias.name))
                    if alias.name.startswith(FORBIDDEN_LOCAL_PREFIXES):
                        violations.append((path.name, alias.name))
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    continue
                module = node.module or ""
                root = _root_name(module)
                if root not in STDLIB and root not in LOCAL_ROOTS:
                    violations.append((path.name, module))
                if module.startswith(FORBIDDEN_LOCAL_PREFIXES):
                    violations.append((path.name, module))
    assert violations == []
