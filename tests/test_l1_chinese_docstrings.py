import ast
import re
from pathlib import Path

L1_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l1_ports"
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")


def _has_chinese(text: str | None) -> bool:
    return bool(text and CHINESE_RE.search(text))


def test_l1_modules_and_public_classes_have_chinese_docstrings():
    violations = []
    for path in L1_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if not _has_chinese(ast.get_docstring(tree)):
            violations.append((path.name, "module"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                if not _has_chinese(ast.get_docstring(node)):
                    violations.append((path.name, node.name))
    assert violations == []
