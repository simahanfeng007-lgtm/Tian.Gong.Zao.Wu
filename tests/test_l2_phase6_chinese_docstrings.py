import ast
import re
from pathlib import Path


L2_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l2_state"
PHASE6_FILES = {
    "memory_state.py",
    "context_state.py",
    "retrieval_state.py",
    "learning_state.py",
    "knowledge_reference_state.py",
}
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")


def test_l2_phase6_modules_and_public_classes_have_chinese_state_docstrings():
    violations = []
    for path in L2_DIR.glob("*.py"):
        if path.name not in PHASE6_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module_doc = ast.get_docstring(tree)
        if not module_doc or not CHINESE_RE.search(module_doc):
            violations.append((path.name, "module", "no_chinese"))
        if not module_doc or "作用" not in module_doc or "边界" not in module_doc:
            violations.append((path.name, "module", "missing_shape"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                doc = ast.get_docstring(node)
                if not doc or not CHINESE_RE.search(doc):
                    violations.append((path.name, node.name, "no_chinese"))
                if not doc or "作用" not in doc or "边界" not in doc:
                    violations.append((path.name, node.name, "missing_shape"))
                is_enum = any(isinstance(base, ast.Name) and base.id == "Enum" for base in node.bases)
                if doc and "状态对象" not in doc and not is_enum:
                    violations.append((path.name, node.name, "not_state_object"))
    assert violations == []
