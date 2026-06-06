import ast
from dataclasses import fields, is_dataclass
from pathlib import Path

PHASE4_MODULES = {"state.py", "lifecycle.py", "failure.py", "transaction.py", "deletion.py"}
L0_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l0_primitives"
FORBIDDEN_CLASS_NAMES = {
    "Runtime", "ToolExecutor", "PluginHost", "ModelClient", "MemorySystem", "PolicyEngine", "RecoveryEngine",
    "StateMachine", "RecoveryAlgorithm", "TransactionExecutor", "SagaOrchestrator", "DeletionExecutor", "SelfHealingAlgorithm",
}
FORBIDDEN_FUNCTION_NAMES = {
    "replay", "restore", "persist", "load", "save", "start", "stop", "run", "schedule",
    "detect_failure", "heal", "recover", "commit_transaction", "rollback_transaction", "execute_saga",
    "delete_file", "erase_data", "redact_content", "issue_lease", "validate_lease", "execute",
}
FORBIDDEN_FIELD_NAMES = {
    "executor", "client", "callback", "callable", "socket", "connection", "file_handle", "process",
    "resource_handle", "database", "session", "transport",
}


def test_phase4_modules_do_not_define_upper_layer_classes_or_flow_functions():
    violations = []
    for path in sorted(L0_DIR.glob("*.py")):
        if path.name not in PHASE4_MODULES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in FORBIDDEN_CLASS_NAMES:
                violations.append((path.name, "class", node.name))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in FORBIDDEN_FUNCTION_NAMES:
                violations.append((path.name, "function", node.name))
    assert violations == []


def test_phase4_ref_dataclasses_do_not_hold_runtime_handles():
    import tiangong_kernel.l0_primitives.deletion as deletion
    import tiangong_kernel.l0_primitives.failure as failure
    import tiangong_kernel.l0_primitives.lifecycle as lifecycle
    import tiangong_kernel.l0_primitives.state as state
    import tiangong_kernel.l0_primitives.transaction as transaction

    violations = []
    for module in (deletion, failure, lifecycle, state, transaction):
        for obj in module.__dict__.values():
            if isinstance(obj, type) and obj.__module__ == module.__name__ and obj.__name__.endswith("Ref") and is_dataclass(obj):
                for field in fields(obj):
                    if field.name in FORBIDDEN_FIELD_NAMES:
                        violations.append((obj.__name__, field.name))
    assert violations == []
