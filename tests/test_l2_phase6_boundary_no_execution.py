import ast
from pathlib import Path


L2_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l2_state"
PHASE6_FILES = {
    "memory_state.py",
    "context_state.py",
    "retrieval_state.py",
    "learning_state.py",
    "knowledge_reference_state.py",
}
FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "asyncio",
    "http",
    "httpx",
    "multiprocessing",
    "os",
    "pathlib",
    "requests",
    "socket",
    "sqlite3",
    "subprocess",
    "threading",
    "urllib",
}
FORBIDDEN_CALL_NAMES = {
    "compile",
    "eval",
    "exec",
    "input",
    "open",
    "print",
}
FORBIDDEN_ATTR_CALLS = {
    "Popen",
    "Thread",
    "connect",
    "create_task",
    "embed",
    "embedding",
    "get",
    "open",
    "query",
    "read",
    "read_bytes",
    "read_text",
    "request",
    "run",
    "search",
    "send",
    "write_bytes",
    "write_text",
}
FORBIDDEN_METHOD_NAMES = {
    "compress",
    "execute",
    "invoke",
    "call_model",
    "call_tool",
    "retrieve",
    "search",
    "query",
    "embed",
    "rank",
    "learn",
    "train",
    "promote",
    "validate",
    "rollback",
    "recover",
    "evolve",
    "experiment",
}
FORBIDDEN_CLASS_NAME_PARTS = {
    "Candidate",
    "Change",
    "Iteration",
    "Evolution",
    "Experiment",
    "Validation",
    "Recovery",
    "SkillSeed",
    "SkillVersion",
    "SkillPatch",
    "AbilityPackage",
    "CapabilityPort",
}
FORBIDDEN_LOCAL_PREFIXES = (
    "tiangong_kernel.l3_",
    "tiangong_kernel.l4_",
    "tiangong_kernel.l5_",
    "tiangong_kernel.l6_",
    "tiangong_kernel.runtime",
    "tiangong_kernel.agent_core",
    "tiangong_kernel.ability",
    "tiangong_kernel.capability",
    "tiangong_kernel.plugin_host",
)


def test_l2_phase6_contains_no_real_io_network_model_tool_retrieval_or_learning_calls():
    violations = []
    for path in L2_DIR.glob("*.py"):
        if path.name not in PHASE6_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root in FORBIDDEN_IMPORT_ROOTS:
                        violations.append((path.name, "import", alias.name))
                    if alias.name.startswith(FORBIDDEN_LOCAL_PREFIXES):
                        violations.append((path.name, "upper_import", alias.name))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                root = module.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    violations.append((path.name, "from", module))
                if module.startswith(FORBIDDEN_LOCAL_PREFIXES):
                    violations.append((path.name, "upper_from", module))
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in FORBIDDEN_CALL_NAMES:
                    violations.append((path.name, "call", func.id))
                elif isinstance(func, ast.Attribute) and func.attr in FORBIDDEN_ATTR_CALLS:
                    violations.append((path.name, "call_attr", func.attr))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in FORBIDDEN_METHOD_NAMES:
                    violations.append((path.name, "method", node.name))
            elif isinstance(node, ast.ClassDef):
                for forbidden in FORBIDDEN_CLASS_NAME_PARTS:
                    if forbidden in node.name:
                        violations.append((path.name, "class", node.name))
    assert violations == []


def test_l2_phase6_does_not_define_phase7_state_objects():
    class_names = []
    for path in L2_DIR.glob("*.py"):
        if path.name not in PHASE6_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        class_names.extend(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    forbidden = (
        "CandidateState",
        "ChangeState",
        "IterationState",
        "EvolutionState",
        "ExperimentState",
        "ValidationState",
        "RecoveryState",
    )
    assert not set(class_names).intersection(forbidden)
