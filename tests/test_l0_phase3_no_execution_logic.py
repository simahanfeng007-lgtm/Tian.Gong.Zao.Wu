import ast
from dataclasses import fields, is_dataclass
from pathlib import Path

PHASE3_MODULES = {
    "actor.py",
    "scope.py",
    "goal.py",
    "plan.py",
    "action.py",
    "effect.py",
    "decision.py",
    "risk.py",
    "grant_lease.py",
}
L0_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l0_primitives"
FORBIDDEN_CLASS_NAMES = {
    "ActorRuntime",
    "ActorLoop",
    "ActorMailbox",
    "ActorMemory",
    "ActorToolUse",
    "ActorPolicy",
    "ActorScheduler",
    "ActorPlugin",
    "Runtime",
    "ToolExecutor",
    "PluginHost",
    "ModelClient",
    "MemorySystem",
    "PolicyEngine",
}
FORBIDDEN_FUNCTION_NAMES = {
    "issue_lease",
    "validate_lease",
    "consume_lease",
    "renew_lease",
    "revoke_lease",
    "execute",
    "run",
    "dispatch",
    "schedule",
    "score_risk",
    "allow",
    "deny",
}
FORBIDDEN_FIELD_NAMES = {
    "executor",
    "client",
    "callback",
    "callable",
    "socket",
    "connection",
    "file_handle",
    "process",
}


def test_phase3_modules_do_not_define_upper_layer_classes_or_flow_functions():
    violations = []
    for path in sorted(L0_DIR.glob("*.py")):
        if path.name not in PHASE3_MODULES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in FORBIDDEN_CLASS_NAMES:
                violations.append((path.name, "class", node.name))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in FORBIDDEN_FUNCTION_NAMES:
                violations.append((path.name, "function", node.name))
    assert violations == []


def test_phase3_ref_dataclasses_do_not_hold_runtime_handles():
    import tiangong_kernel.l0_primitives.action as action
    import tiangong_kernel.l0_primitives.actor as actor
    import tiangong_kernel.l0_primitives.decision as decision
    import tiangong_kernel.l0_primitives.effect as effect
    import tiangong_kernel.l0_primitives.goal as goal
    import tiangong_kernel.l0_primitives.grant_lease as grant_lease
    import tiangong_kernel.l0_primitives.plan as plan
    import tiangong_kernel.l0_primitives.risk as risk
    import tiangong_kernel.l0_primitives.scope as scope

    violations = []
    for module in (action, actor, decision, effect, goal, grant_lease, plan, risk, scope):
        for obj in module.__dict__.values():
            if isinstance(obj, type) and obj.__module__ == module.__name__ and obj.__name__.endswith("Ref") and is_dataclass(obj):
                for field in fields(obj):
                    if field.name in FORBIDDEN_FIELD_NAMES:
                        violations.append((obj.__name__, field.name))
    assert violations == []
