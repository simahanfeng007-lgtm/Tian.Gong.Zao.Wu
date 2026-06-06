import ast
from pathlib import Path

L0_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l0_primitives"
FORBIDDEN_IMPORT_ROOTS = {"socket", "subprocess", "requests", "urllib", "http", "ftplib", "smtplib", "pathlib", "os"}
FORBIDDEN_CALL_NAMES = {"open", "input", "print", "exec", "eval", "compile"}
FORBIDDEN_ATTR_CALLS = {
    "read_text",
    "write_text",
    "read_bytes",
    "write_bytes",
    "open",
    "mkdir",
    "unlink",
    "rename",
    "replace",
    "remove",
    "rmdir",
    "system",
    "popen",
    "run",
    "Popen",
    "urlopen",
}


def test_l0_contains_no_real_io_or_process_calls():
    violations = []
    for path in L0_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in FORBIDDEN_IMPORT_ROOTS:
                        violations.append((path.name, "import", alias.name))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.split(".", 1)[0] in FORBIDDEN_IMPORT_ROOTS:
                    violations.append((path.name, "from", module))
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in FORBIDDEN_CALL_NAMES:
                    violations.append((path.name, "call", func.id))
                elif isinstance(func, ast.Attribute) and func.attr in FORBIDDEN_ATTR_CALLS:
                    violations.append((path.name, "call_attr", func.attr))
    assert violations == []
