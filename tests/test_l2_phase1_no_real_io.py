import ast
from pathlib import Path


L2_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l2_state"
FORBIDDEN_IMPORT_ROOTS = {
    "asyncio",
    "ftplib",
    "http",
    "httpx",
    "multiprocessing",
    "os",
    "pathlib",
    "requests",
    "smtplib",
    "socket",
    "sqlite3",
    "subprocess",
    "threading",
    "urllib",
}
FORBIDDEN_CALL_NAMES = {"compile", "eval", "exec", "input", "open", "print"}
FORBIDDEN_ATTR_CALLS = {
    "Thread",
    "Popen",
    "connect",
    "create_task",
    "mkdir",
    "open",
    "popen",
    "read_bytes",
    "read_text",
    "remove",
    "rename",
    "replace",
    "rmdir",
    "run",
    "system",
    "unlink",
    "urlopen",
    "write_bytes",
    "write_text",
}
FORBIDDEN_TEXT = {
    "Path.read_text",
    "Path.write_text",
    "StateStore",
    "client.chat",
    "execute_plan",
    "invoke_tool",
    "model.call",
    "release_tool",
    "run_loop",
    "select_skill",
    "tool.call",
    "PluginHost",
    "ToolExecutor",
    "ModelExecutor",
    "SchedulerEngine",
}


def test_l2_phase1_contains_no_real_io_network_process_or_runtime_calls():
    violations = []
    for path in L2_DIR.glob("*.py"):
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
    assert violations == []
