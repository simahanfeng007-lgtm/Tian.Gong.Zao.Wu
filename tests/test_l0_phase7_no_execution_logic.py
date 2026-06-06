import ast
from dataclasses import fields, is_dataclass
from pathlib import Path

PHASE7_MODULES = {"resource.py", "cost_budget.py", "environment.py", "location.py", "communication.py", "tool_adapter.py", "skill_capability.py", "component_package.py"}
L0_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l0_primitives"
FORBIDDEN_CLASS_NAMES = {"ResourceManager", "SandboxManager", "CommunicationBus", "ToolRegistry", "SkillSystem", "PackageManager", "Runtime", "ToolExecutor", "PluginHost", "ModelClient", "MemorySystem", "PolicyEngine"}
FORBIDDEN_FUNCTION_NAMES = {"allocate", "release", "collect_usage", "manage_resource", "charge", "throttle", "route_model", "optimize_budget", "count_tokens", "start_container", "run_process", "mount", "set_network_policy", "browser_control", "open", "read", "write", "resolve_uri", "fetch", "normalize_path", "send", "receive", "route", "retry", "connect", "execute_tool", "call_tool", "run_skill", "select_capability", "compose_skill", "load_plugin", "import_module", "install_package", "resolve_dependency", "hot_reload"}
FORBIDDEN_FIELD_NAMES = {"executor", "client", "callback", "callable", "socket", "connection", "file_handle", "process", "resource_handle", "database", "transport", "mutable_object", "real_handle"}
FORBIDDEN_TEXT_TOKENS = {"ResourceManager", "SandboxManager", "CommunicationBus", "ToolRegistry", "SkillSystem", "PackageManager", "ToolExecutor", "PluginHost", "ModelClient", "MemorySystem", "PolicyEngine", "execute_tool", "call_tool", "run_skill", "select_capability", "compose_skill", "load_plugin", "import_module", "install_package", "resolve_dependency", "hot_reload", "route_model", "optimize_budget", "count_tokens", "start_container", "run_process", "set_network_policy", "browser_control", "resolve_uri", "normalize_path"}

def test_phase7_modules_do_not_define_upper_layer_classes_or_flow_functions():
    violations = []
    for path in sorted(L0_DIR.glob("*.py")):
        if path.name not in PHASE7_MODULES:
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

def test_phase7_ref_dataclasses_do_not_hold_runtime_handles():
    import tiangong_kernel.l0_primitives.communication as communication
    import tiangong_kernel.l0_primitives.component_package as component_package
    import tiangong_kernel.l0_primitives.cost_budget as cost_budget
    import tiangong_kernel.l0_primitives.environment as environment
    import tiangong_kernel.l0_primitives.location as location
    import tiangong_kernel.l0_primitives.resource as resource
    import tiangong_kernel.l0_primitives.skill_capability as skill_capability
    import tiangong_kernel.l0_primitives.tool_adapter as tool_adapter
    violations = []
    for module in (resource, cost_budget, environment, location, communication, tool_adapter, skill_capability, component_package):
        for obj in module.__dict__.values():
            if isinstance(obj, type) and obj.__module__ == module.__name__ and obj.__name__.endswith("Ref") and is_dataclass(obj):
                for field in fields(obj):
                    if field.name in FORBIDDEN_FIELD_NAMES:
                        violations.append((obj.__name__, field.name))
    assert violations == []
