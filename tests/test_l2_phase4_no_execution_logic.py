import ast
import inspect
from enum import Enum
from pathlib import Path

import tiangong_kernel.l2_state.boundary_state as boundary_state
import tiangong_kernel.l2_state.control_state as control_state
import tiangong_kernel.l2_state.environment_state as environment_state
import tiangong_kernel.l2_state.resource_state as resource_state
import tiangong_kernel.l2_state.risk_decision_state as risk_decision_state
import tiangong_kernel.l2_state.security_state as security_state


L2_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l2_state"
PHASE4_FILES = {
    "control_state.py",
    "boundary_state.py",
    "risk_decision_state.py",
    "resource_state.py",
    "environment_state.py",
    "security_state.py",
}
MODULES = (
    control_state,
    boundary_state,
    risk_decision_state,
    resource_state,
    environment_state,
    security_state,
)
FORBIDDEN_PUBLIC_METHODS = {
    "execute",
    "invoke",
    "call_tool",
    "call_model",
    "release_tool_group",
    "select_skill",
    "schedule",
    "restore",
    "checkpoint",
    "load_plugin",
    "score_risk",
    "calculate_risk",
    "decide",
    "allow",
    "deny",
    "probe_environment",
    "scan_security",
    "read_secret",
    "consume_budget",
    "reserve_quota",
}


def _public_local_classes(module):
    for _, value in inspect.getmembers(module, inspect.isclass):
        if value.__module__ == module.__name__ and not value.__name__.startswith("_"):
            yield value


def test_l2_phase4_public_classes_expose_no_execution_or_decision_methods():
    violations = []
    for module in MODULES:
        for cls in _public_local_classes(module):
            if issubclass(cls, Enum):
                continue
            for name, _ in inspect.getmembers(cls, inspect.isfunction):
                if name in FORBIDDEN_PUBLIC_METHODS:
                    violations.append((cls.__name__, name))
    assert violations == []


def test_l2_phase4_source_defines_no_forbidden_execution_functions():
    violations = []
    for path in L2_DIR.glob("*.py"):
        if path.name not in PHASE4_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in FORBIDDEN_PUBLIC_METHODS:
                    violations.append((path.name, node.name))
    assert violations == []
