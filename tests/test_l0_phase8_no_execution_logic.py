import ast
from dataclasses import fields, is_dataclass
from pathlib import Path

PHASE8_MODULES = {"artifact.py", "evidence.py", "audit.py", "versioning.py", "namespace.py", "relation.py", "retrieval.py", "validation.py", "schedule.py"}
L0_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l0_primitives"
FORBIDDEN_CLASS_NAMES = {"Runtime", "ToolExecutor", "PluginHost", "ModelClient", "MemorySystem", "PolicyEngine", "AuditSystem", "SchemaRegistry", "GraphDatabase", "RetrievalEngine", "TestRunner", "SchedulerEngine"}
FORBIDDEN_FUNCTION_NAMES = {"create_file", "write_file", "build_archive", "render", "export", "collect_evidence", "verify_evidence", "scan_log", "generate_report", "sign", "encrypt", "migrate", "run_migration", "upcast_object", "codegen", "resolve_name", "register_name", "service_discovery", "traverse_graph", "topological_sort", "infer_relation", "vector_search", "full_text_search", "rank_results", "sql_execute", "run_test", "evaluate_model", "verify_runtime", "benchmark", "schedule_job", "start_timer", "wakeup_now"}
FORBIDDEN_TEXT_TOKENS = {"create_file", "write_file", "build_archive", "collect_evidence", "verify_evidence", "scan_log", "generate_report", "write_audit_log", "run_migration", "upcast_object", "codegen", "resolve_name", "register_name", "service_discovery", "import_module", "traverse_graph", "topological_sort", "infer_relation", "graph_db", "vector_search", "full_text_search", "rank_results", "sql_execute", "run_test", "evaluate_model", "verify_runtime", "schedule_job", "start_timer", "wakeup_now"}
FORBIDDEN_FIELD_NAMES = {"executor", "client", "callback", "callable", "socket", "connection", "file_handle", "process", "resource_handle", "database", "transport", "mutable_object", "real_handle"}


def test_phase8_modules_do_not_define_upper_layer_classes_or_flow_functions():
    violations = []
    for path in sorted(L0_DIR.glob("*.py")):
        if path.name not in PHASE8_MODULES:
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


def test_phase8_ref_dataclasses_do_not_hold_runtime_handles():
    import tiangong_kernel.l0_primitives.artifact as artifact
    import tiangong_kernel.l0_primitives.audit as audit
    import tiangong_kernel.l0_primitives.evidence as evidence
    import tiangong_kernel.l0_primitives.namespace as namespace
    import tiangong_kernel.l0_primitives.relation as relation
    import tiangong_kernel.l0_primitives.retrieval as retrieval
    import tiangong_kernel.l0_primitives.schedule as schedule
    import tiangong_kernel.l0_primitives.validation as validation
    import tiangong_kernel.l0_primitives.versioning as versioning
    violations = []
    for module in (artifact, evidence, audit, versioning, namespace, relation, retrieval, validation, schedule):
        for obj in module.__dict__.values():
            if isinstance(obj, type) and obj.__module__ == module.__name__ and obj.__name__.endswith("Ref") and is_dataclass(obj):
                for field in fields(obj):
                    if field.name in FORBIDDEN_FIELD_NAMES:
                        violations.append((obj.__name__, field.name))
    assert violations == []
