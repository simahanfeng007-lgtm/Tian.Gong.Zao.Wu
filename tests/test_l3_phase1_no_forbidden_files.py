from pathlib import Path


L3_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l3_orchestration"
FORBIDDEN_FILES = {
    "run_orchestrator.py",
    "task_orchestrator.py",
    "skill_orchestrator.py",
    "tool_group_orchestrator.py",
    "boundary_orchestrator.py",
    "execution_dispatcher.py",
    "subsystem_router.py",
    "recovery_orchestrator.py",
    "evolution_orchestrator.py",
    "affective_engine.py",
    "learning_engine.py",
    "risk_engine.py",
    "model_client.py",
    "tool_executor.py",
    "state_store.py",
    "plugin_host.py",
}
EXPECTED_FILES = {
    "__init__.py",
    "orchestration_identity.py",
    "orchestration_status.py",
    "orchestration_request.py",
    "orchestration_context.py",
    "orchestration_step.py",
    "orchestration_plan.py",
    "orchestration_result.py",
    "orchestration_transition.py",
    "orchestration_invariant.py",
    "orchestration_error.py",
    "orchestration_serialization.py",
    "orchestration_math.py",
    "orchestration_math_input.py",
    "orchestration_math_result.py",
}


def test_l3_phase1_contains_only_expected_source_files_and_no_forbidden_orchestrators():
    names = {path.name for path in L3_DIR.glob("*.py")}
    assert EXPECTED_FILES.issubset(names)
    assert names.isdisjoint(FORBIDDEN_FILES)
