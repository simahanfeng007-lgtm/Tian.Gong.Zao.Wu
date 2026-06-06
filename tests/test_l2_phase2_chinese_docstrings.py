import ast
import re
from pathlib import Path


L2_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l2_state"
PHASE2_FILES = {
    "agent_state.py",
    "run_state.py",
    "task_state.py",
    "goal_plan_state.py",
    "state_lifecycle.py",
    "continuity_state.py",
}
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
BOUNDARY_WORDS = ("不执行", "不调度", "不调用模型", "不调用模型或工具", "不保存", "不恢复", "不回滚")


def _has_chinese(text: str | None) -> bool:
    return bool(text and CHINESE_RE.search(text))


def test_l2_phase2_modules_and_public_classes_have_chinese_boundary_docstrings():
    violations = []
    for path in L2_DIR.glob("*.py"):
        if path.name not in PHASE2_FILES:
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
                if not doc or not any(word in doc for word in BOUNDARY_WORDS):
                    violations.append((path.name, node.name, "missing_boundary_phrase"))
    assert violations == []
