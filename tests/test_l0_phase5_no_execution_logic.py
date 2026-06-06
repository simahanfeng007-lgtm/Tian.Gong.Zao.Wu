import ast
from dataclasses import fields, is_dataclass
from pathlib import Path

PHASE5_MODULES = {"memory.py", "forgetting.py", "context.py", "learning.py", "health.py"}
L0_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l0_primitives"
FORBIDDEN_CLASS_NAMES = {
    "Runtime", "ToolExecutor", "PluginHost", "ModelClient", "MemorySystem", "ForgettingSystem",
    "SelfHealingSystem", "HealthMonitor", "PolicyEngine", "MemoryStore", "MemoryRetriever",
    "VectorMemory", "GraphMemory", "ContextBuilder", "ContextSelector", "ContextCompressor",
    "ForgettingScheduler",
}
FORBIDDEN_FUNCTION_NAMES = {
    "recall", "retrieve", "store", "write", "consolidate", "recall_memory", "write_memory",
    "consolidate_memory", "search_memory", "forget", "decay", "prune", "suppress",
    "forget_memory", "decay_memory", "prune_memory", "suppress_memory", "sleep_cleanup",
    "delete_real_data", "build_context", "compress_context", "inject_memory", "train",
    "fine_tune", "evolve", "merge", "modify_code", "generate_tool", "score_health",
    "trigger_recovery", "monitor", "collect_metrics", "execute", "run", "schedule",
}
FORBIDDEN_FIELD_NAMES = {
    "executor", "client", "callback", "callable", "socket", "connection", "file_handle", "process",
    "resource_handle", "database", "transport", "mutable_object", "real_handle",
}
FORBIDDEN_TEXT_TOKENS = {
    "ToolExecutor", "PluginHost", "ModelClient", "MemorySystem", "ForgettingSystem",
    "SelfHealingSystem", "HealthMonitor", "PolicyEngine", "MemoryStore", "MemoryRetriever",
    "VectorMemory", "GraphMemory", "ContextBuilder", "ContextSelector", "ContextCompressor",
    "prompt builder", "system prompt", "reward model",
}


def test_phase5_modules_do_not_define_upper_layer_classes_or_flow_functions():
    violations = []
    for path in sorted(L0_DIR.glob("*.py")):
        if path.name not in PHASE5_MODULES:
            continue
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TEXT_TOKENS:
            if token in text:
                violations.append((path.name, "text", token))
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in FORBIDDEN_CLASS_NAMES:
                violations.append((path.name, "class", node.name))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in FORBIDDEN_FUNCTION_NAMES:
                violations.append((path.name, "function", node.name))
    assert violations == []


def test_phase5_ref_dataclasses_do_not_hold_runtime_handles():
    import tiangong_kernel.l0_primitives.context as context
    import tiangong_kernel.l0_primitives.forgetting as forgetting
    import tiangong_kernel.l0_primitives.health as health
    import tiangong_kernel.l0_primitives.learning as learning
    import tiangong_kernel.l0_primitives.memory as memory

    violations = []
    for module in (memory, forgetting, context, learning, health):
        for obj in module.__dict__.values():
            if isinstance(obj, type) and obj.__module__ == module.__name__ and obj.__name__.endswith("Ref") and is_dataclass(obj):
                for field in fields(obj):
                    if field.name in FORBIDDEN_FIELD_NAMES:
                        violations.append((obj.__name__, field.name))
    assert violations == []
