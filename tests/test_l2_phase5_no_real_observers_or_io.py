import ast
from pathlib import Path


L2_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l2_state"
PHASE5_FILES = {
    "observation_source_state.py",
    "observation_channel_state.py",
    "observation_frame_state.py",
    "event_stream_state.py",
    "observation_metric_state.py",
    "audit_observation_state.py",
    "observation_quality_state.py",
    "observation_projection_state.py",
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
    "Popen",
    "Thread",
    "connect",
    "create_task",
    "environ",
    "open",
    "read_bytes",
    "read_text",
    "run",
    "write_bytes",
    "write_text",
}
FORBIDDEN_METHOD_NAMES = {
    "observe",
    "watch",
    "listen",
    "collect",
    "sample",
    "poll",
    "read_log",
    "read_metric",
    "trace",
    "emit",
    "write_audit",
    "stream",
    "subscribe",
    "consume",
    "execute",
    "invoke",
    "call_model",
    "call_tool",
    "recover",
}


def test_l2_phase5_contains_no_real_observer_io_network_or_process_calls():
    violations = []
    for path in L2_DIR.glob("*.py"):
        if path.name not in PHASE5_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root in FORBIDDEN_IMPORT_ROOTS:
                        violations.append((path.name, "import", alias.name))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                root = module.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    violations.append((path.name, "from", module))
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
