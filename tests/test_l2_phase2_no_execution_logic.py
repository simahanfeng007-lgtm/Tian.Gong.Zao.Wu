import ast
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
FORBIDDEN_NAMES = {
    "run_loop",
    "execute",
    "restore",
    "rollback",
    "schedule",
    "select_skill",
    "release_tool",
    "invoke_tool",
    "call_model",
    "call_tool",
}


def test_l2_phase2_source_has_no_execution_methods_or_calls():
    violations = []
    for path in L2_DIR.glob("*.py"):
        if path.name not in PHASE2_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in FORBIDDEN_NAMES:
                    violations.append((path.name, "function", node.name))
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in FORBIDDEN_NAMES:
                    violations.append((path.name, "call", func.id))
                elif isinstance(func, ast.Attribute) and func.attr in FORBIDDEN_NAMES:
                    violations.append((path.name, "call_attr", func.attr))
    assert violations == []
