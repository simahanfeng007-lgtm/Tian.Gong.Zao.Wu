import ast
import re
from pathlib import Path


L2_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l2_state"
PHASE4_FILES = {
    "control_state.py",
    "boundary_state.py",
    "risk_decision_state.py",
    "resource_state.py",
    "environment_state.py",
    "security_state.py",
}
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
FORBIDDEN_HINTS = ("会执行", "会调用模型", "会调用工具", "会调度", "会读取密钥")


def _has_chinese(text: str | None) -> bool:
    return bool(text and CHINESE_RE.search(text))


def test_l2_phase4_modules_and_public_classes_have_chinese_boundary_docstrings():
    violations = []
    for path in L2_DIR.glob("*.py"):
        if path.name not in PHASE4_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module_doc = ast.get_docstring(tree)
        if not _has_chinese(module_doc):
            violations.append((path.name, "module", "no_chinese"))
        if not module_doc or "作用" not in module_doc or "边界" not in module_doc:
            violations.append((path.name, "module", "missing_shape"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                doc = ast.get_docstring(node)
                if not _has_chinese(doc):
                    violations.append((path.name, node.name, "no_chinese"))
                if not doc or "作用" not in doc or "边界" not in doc:
                    violations.append((path.name, node.name, "missing_shape"))
                if doc and any(text in doc for text in FORBIDDEN_HINTS):
                    violations.append((path.name, node.name, "implies_execution"))
    assert violations == []
