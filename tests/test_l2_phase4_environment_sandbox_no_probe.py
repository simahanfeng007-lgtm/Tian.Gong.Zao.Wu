import ast
from pathlib import Path

from tiangong_kernel.l2_state import EnvironmentKind, EnvironmentStatus, SandboxStatus
from tests.test_l2_phase4_serialization import build_phase4_objects


ENVIRONMENT_FILE = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l2_state" / "environment_state.py"


def test_l2_phase4_environment_and_sandbox_record_refs_only():
    objects = build_phase4_objects()
    environment = objects["environment"]
    sandbox = objects["sandbox"]
    external = objects["external"]

    assert environment.environment_kind is EnvironmentKind.SANDBOX
    assert environment.environment_status is EnvironmentStatus.AVAILABLE_RECORDED
    assert environment.sandbox_state_ref == sandbox.identity.state_ref
    assert sandbox.sandbox_status is SandboxStatus.LIMITED_RECORDED
    assert sandbox.trust_boundary_ref is not None
    assert external.external_ref is not None
    assert external.access_status is EnvironmentStatus.LIMITED_RECORDED


def test_l2_phase4_environment_source_contains_no_probe_calls():
    tree = ast.parse(ENVIRONMENT_FILE.read_text(encoding="utf-8"), filename=str(ENVIRONMENT_FILE))
    forbidden_import_roots = {"os", "platform", "socket", "subprocess", "pathlib"}
    forbidden_attr_calls = {"getenv", "system", "gethostname", "home", "iterdir", "read_text", "write_text"}
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in forbidden_import_roots:
                    violations.append(("import", alias.name))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".", 1)[0] in forbidden_import_roots:
                violations.append(("from", module))
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in forbidden_attr_calls:
                violations.append(("call_attr", func.attr))
    assert violations == []
