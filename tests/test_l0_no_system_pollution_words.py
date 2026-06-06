import ast
from pathlib import Path

L0_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l0_primitives"
FORBIDDEN_IMPLEMENTATION_NAMES = {
    "RuntimeLoop",
    "ToolExecutor",
    "PluginHost",
    "ModelClient",
    "MemorySystem",
    "ForgettingSystem",
    "SelfHealingSystem",
    "PolicyEngine",
    "SecurityEngine",
    "PrivacyEngine",
    "SchedulerEngine",
    "RecoveryEngine",
    "Gateway",
    "Frontend",
    "Database",
    "VectorDB",
    "GraphDB",
    "HTTPClient",
    "ShellExecutor",
    "FileSystemTool",
}


def test_l0_has_no_upper_layer_implementation_symbols():
    violations = []
    for path in L0_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in FORBIDDEN_IMPLEMENTATION_NAMES:
                    violations.append((path.name, type(node).__name__, node.name))
            elif isinstance(node, ast.Name):
                if node.id in FORBIDDEN_IMPLEMENTATION_NAMES:
                    violations.append((path.name, "Name", node.id))
    assert violations == []
