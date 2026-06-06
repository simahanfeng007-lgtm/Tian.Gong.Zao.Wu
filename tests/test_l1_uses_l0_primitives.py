import ast
from pathlib import Path

L1_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l1_ports"


def test_l1_source_imports_l0_primitives_directly():
    imports = set()
    for path in L1_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith("tiangong_kernel.l0_primitives"):
                    imports.add((path.name, module))
    modules = {item[0] for item in imports}
    assert "base.py" in modules
    assert "port_result.py" in modules
    assert "envelope.py" in modules
    assert len(imports) >= 6
