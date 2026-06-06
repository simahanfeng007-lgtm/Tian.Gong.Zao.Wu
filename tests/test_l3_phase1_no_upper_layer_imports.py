import ast
from pathlib import Path


L3_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l3_orchestration"
FORBIDDEN_LOCAL_PREFIXES = (
    "tiangong_kernel.l4",
    "tiangong_kernel.l5",
    "tiangong_kernel.l6",
    "tiangong_kernel.runtime",
    "tiangong_kernel.agent_core",
    "tiangong_kernel.ability",
    "tiangong_kernel.capability",
    "tiangong_kernel.plugin_host",
)


def test_l3_phase1_has_no_upper_layer_or_legacy_imports():
    violations = []
    for path in L3_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(FORBIDDEN_LOCAL_PREFIXES):
                        violations.append((path.name, alias.name))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith(FORBIDDEN_LOCAL_PREFIXES):
                    violations.append((path.name, module))
    assert violations == []
