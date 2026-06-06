import ast
from pathlib import Path


L2_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l2_state"
PHASE9_FILES = {
    "__init__.py",
    "affective_state.py",
    "component_state.py",
    "dynamic_drive_state.py",
    "math_state.py",
    "projection_state.py",
    "state_identity.py",
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
FORBIDDEN_CALL_NAMES = {"compile", "eval", "exec", "input", "open", "print"}
FORBIDDEN_ATTR_CALLS = {
    "connect",
    "create_task",
    "glob",
    "iterdir",
    "mkdir",
    "open",
    "read_bytes",
    "read_text",
    "request",
    "run",
    "send",
    "unlink",
    "write_bytes",
    "write_text",
}
FORBIDDEN_METHOD_NAMES = {
    "calculate_score",
    "rank",
    "train_model",
    "call_model",
    "call_tool",
    "select_skill",
    "release_tool",
    "decide_permission",
    "apply_patch",
    "rollback",
    "run_validation",
    "create_candidate",
}
FORBIDDEN_TEXT = {
    "CapabilityPort",
    "AbilityPackagePort",
    "AbilityRouter",
    "AbilityExecutor",
    "client.chat",
    "Path.read_text",
    "Path.write_text",
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


def test_l2_phase9_contains_no_real_io_network_model_tool_or_decision_calls():
    violations = []
    for path in L2_DIR.glob("*.py"):
        if path.name not in PHASE9_FILES:
            continue
        source = path.read_text(encoding="utf-8")
        for text in FORBIDDEN_TEXT:
            if text in source:
                violations.append((path.name, "text", text))
        tree = ast.parse(source, filename=str(path))
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
    assert violations == []


def test_l2_phase9_state_objects_remain_dataclass_facts_without_public_methods():
    violations = []
    for path in L2_DIR.glob("*.py"):
        if path.name not in PHASE9_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name != "__post_init__":
                        violations.append((path.name, node.name, item.name))
    assert violations == []
