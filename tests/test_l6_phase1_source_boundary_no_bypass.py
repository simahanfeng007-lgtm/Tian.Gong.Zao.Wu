import ast
from dataclasses import fields, is_dataclass
from pathlib import Path

import tiangong_kernel.l6_plugins.common as common

PROJECT_ROOT = Path(__file__).resolve().parents[1]
L6_COMMON = PROJECT_ROOT / "tiangong_kernel" / "l6_plugins" / "common"
FORBIDDEN_IMPORT_ROOTS = {
    "os", "pathlib", "socket", "subprocess", "requests", "httpx", "urllib", "importlib", "openai", "anthropic",
    "dashscope", "zhipuai", "minimax", "deepseek", "google.genai",
}
FORBIDDEN_LOWER_LAYER_IMPORT_PREFIXES = (
    "tiangong_kernel.l3_",
    "tiangong_kernel.l4_",
    "tiangong_kernel.l5_",
)
FORBIDDEN_FIELD_NAMES = {
    "entrypoint", "entry_point", "callable", "handler", "shell_command", "provider_base_url", "base_url",
    "endpoint", "api_key", "token", "password", "secret", "secret_value", "credential_value", "file_path",
    "database_uri", "tool_handle", "model_client", "l4_adapter", "state_writer", "audit_writer",
}
FORBIDDEN_METHOD_NAMES = {
    "execute", "run", "apply", "commit", "migrate", "rollback", "hot_switch", "replay", "write_state",
    "write_audit", "fetch_secret", "call_model", "call_tool", "invoke_tool",
}


def _imports_for(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def test_l6_common_does_not_import_external_io_provider_or_lower_execution_layers():
    imports = set()
    for path in sorted(L6_COMMON.glob("*.py")):
        imports.update(_imports_for(path))
    roots = {name.split(".")[0] for name in imports}
    assert not (roots & FORBIDDEN_IMPORT_ROOTS)
    assert not any(module.startswith(FORBIDDEN_LOWER_LAYER_IMPORT_PREFIXES) for module in imports)


def test_l6_common_public_dataclasses_do_not_expose_forbidden_field_or_method_names():
    for exported_name in common.__all__:
        obj = getattr(common, exported_name)
        if isinstance(obj, type) and is_dataclass(obj):
            field_names = {field.name for field in fields(obj)}
            assert not (field_names & FORBIDDEN_FIELD_NAMES), f"{exported_name} exposes forbidden fields {field_names & FORBIDDEN_FIELD_NAMES}"
            method_names = {name for name, item in obj.__dict__.items() if callable(item)}
            assert not (method_names & FORBIDDEN_METHOD_NAMES), f"{exported_name} exposes forbidden methods {method_names & FORBIDDEN_METHOD_NAMES}"
