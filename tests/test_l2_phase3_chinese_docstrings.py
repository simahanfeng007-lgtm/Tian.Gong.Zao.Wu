import ast
import re
from pathlib import Path


L2_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l2_state"
PHASE3_FILES = {
    "skill_state.py",
    "tool_group_state.py",
    "tool_intent_state.py",
    "model_state.py",
    "action_effect_state.py",
}
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
FORBIDDEN_HINTS = ("会执行", "会调用模型", "会调用工具", "会调度")


def _has_chinese(text: str | None) -> bool:
    return bool(text and CHINESE_RE.search(text))


def test_l2_phase3_modules_and_public_classes_have_chinese_boundary_docstrings():
    violations = []
    for path in L2_DIR.glob("*.py"):
        if path.name not in PHASE3_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module_doc = ast.get_docstring(tree)
        if not _has_chinese(module_doc):
            violations.append((path.name, "module", "no_chinese"))
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
