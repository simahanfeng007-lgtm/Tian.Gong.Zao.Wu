import ast
from pathlib import Path


L3_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l3_orchestration"
PHASE6_FILES = {
    "observation_feedback.py",
    "context_carryover.py",
    "subsystem_service_request.py",
    "memory_service_request.py",
    "retrieval_service_request.py",
    "learning_service_request.py",
    "affective_service_request.py",
    "candidate_proposal_advice.py",
    "observation_context_math.py",
    "observation_context_transition.py",
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
    "sample_observation",
    "call_model",
    "call_tool",
    "write_memory",
    "run_retrieval",
    "generate_skill",
    "generate_tool",
    "compute_emotion",
    "dispatch_service",
    "apply_candidate",
}
FORBIDDEN_TEXT = {
    "Observer",
    "ObservationEngine",
    "DesktopObserver",
    "FileObserver",
    "NetworkObserver",
    "MemoryStore",
    "MemoryEngine",
    "RetrievalEngine",
    "SearchEngine",
    "EmbeddingEngine",
    "VectorStore",
    "LearningEngine",
    "SkillGenerator",
    "KnowledgeGenerator",
    "ToolGenerator",
    "AffectiveEngine",
    "EmotionEngine",
    "PluginHost",
    "SubsystemRouterRuntime",
    "BoundaryDecision",
    "PermissionDecision",
    "RiskDecision",
    "ExecutionDispatcherRuntime",
    "ExecutionEngine",
    "AbilityPackage",
    "CapabilityPort",
    "AbilityPackagePort",
    "client.chat",
    "chat.completions",
    "tool.execute",
    "invoke_tool",
    "model_client",
    "shenshu",
    "runtime_core",
}
FORBIDDEN_LOCAL_PREFIXES = (
    "tiangong_kernel.l4",
    "tiangong_kernel.l5",
    "tiangong_kernel.l6",
    "tiangong_kernel.runtime",
    "tiangong_kernel.agent_core",
    "tiangong_kernel.ability",
    "tiangong_kernel.capability",
    "tiangong_kernel.plugin_host",
)


def test_l3_phase6_source_has_no_real_l6_services_or_side_effects():
    violations = []
    for path in sorted(L3_DIR.glob("*.py")):
        if path.name not in PHASE6_FILES:
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
                        violations.append((path.name, "local_import", alias.name))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                root = module.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    violations.append((path.name, "from", module))
                if module.startswith(FORBIDDEN_LOCAL_PREFIXES):
                    violations.append((path.name, "local_from", module))
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
