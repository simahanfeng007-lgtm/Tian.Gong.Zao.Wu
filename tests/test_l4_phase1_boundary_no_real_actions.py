import ast
from pathlib import Path

from l4_phase1_builders import build_l4_phase1_objects


PROJECT_ROOT = Path(__file__).resolve().parents[1]
L4_PACKAGE = PROJECT_ROOT / "tiangong_kernel" / "l4_action_grounding"


def _python_files():
    return sorted(L4_PACKAGE.glob("*.py"))


def test_l4_phase1_package_does_not_import_real_action_modules():
    forbidden_modules = {"os", "pathlib", "socket", "subprocess", "requests", "urllib", "httpx", "threading", "multiprocessing"}
    imported = set()
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
    assert forbidden_modules.isdisjoint(imported)


def test_l4_phase1_package_has_no_file_write_network_or_process_calls():
    forbidden_call_names = {"open", "Popen", "call_model", "call_tool", "invoke_tool"}
    forbidden_attrs = {"write", "write_text", "write_bytes", "connect", "request", "post", "get"}
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in forbidden_call_names
                if isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in forbidden_attrs


def test_l4_phase1_runners_report_no_real_actions():
    objects = build_l4_phase1_objects(include_permit=True)
    assert objects["fake_runner"].produces_real_actions is False
    assert objects["dry_runner"].produces_real_actions is False
    assert objects["noop_runner"].produces_real_actions is False
    assert objects["result"].real_action_performed is False
