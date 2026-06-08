from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def _sample_repo(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "calc.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp_path / "tests" / "test_calc.py").write_text("from src.calc import add\n\ndef test_add():\n    assert add(1, 2) == 3\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\npythonpath=['.']\n", encoding="utf-8")
    return tmp_path


def test_codex_tools_registered() -> None:
    runtime = RuntimeEntry()
    names = set(runtime.registry.names())
    required = {
        "code_x_runtime_status",
        "repo_map",
        "issue_to_file_localizer",
        "workspace_patch_applier",
        "python_quality_runner",
        "failure_attribution_analyzer",
        "workspace_snapshot",
        "code_x_package_workflow",
    }
    assert required.issubset(names)


def test_codex_runtime_chain_smoke(tmp_path: Path) -> None:
    repo = _sample_repo(tmp_path)
    runtime = RuntimeEntry()
    plan = [
        ToolInvocation("code_x_runtime_status", {}),
        ToolInvocation("repo_map", {}),
        ToolInvocation("issue_to_file_localizer", {"issue_text": "add function behavior"}),
        ToolInvocation("workspace_snapshot", {}),
        ToolInvocation(
            "workspace_patch_applier",
            {"edit_units": [{"edit_type": "create_file", "path": "src/new_feature.py", "content": "VALUE = 42\n"}]},
        ),
        ToolInvocation("python_quality_runner", {}),
        ToolInvocation("failure_attribution_analyzer", {"log_text": "SyntaxError: invalid syntax"}),
        ToolInvocation("code_x_package_workflow", {"include_paths": ["src"], "output_zip": "dist/code_x_delivery.zip"}),
    ]
    result = runtime.execute_plan(plan, workspace=repo, user_message="code-x runtime chain smoke", max_steps=20)
    assert [item.status.value for item in result.results].count("ok") == len(result.results)
    assert (repo / "src" / "new_feature.py").exists()
    assert (repo / "dist" / "code_x_delivery.zip").exists()


def test_codex_planbridge_triggers(tmp_path: Path) -> None:
    repo = _sample_repo(tmp_path)
    runtime = RuntimeEntry()
    result = runtime.run_text("code-x smoke .", workspace=repo, max_steps=5)
    assert result.plan
    assert result.plan[0].tool_name == "code_x_smoke_workflow"
    assert result.results[0].status.value == "ok"


def test_codex_skill_and_audit_tools_registered(tmp_path: Path) -> None:
    repo = _sample_repo(tmp_path)
    runtime = RuntimeEntry()
    names = set(runtime.registry.names())
    required = {
        "code_x_skill_guide",
        "code_x_world_class_readiness_check",
        "code_x_v1_import_audit",
    }
    assert required.issubset(names)
    result = runtime.execute_plan([
        ToolInvocation("code_x_skill_guide", {"task_type": "bug_fix"}),
        ToolInvocation("code_x_world_class_readiness_check", {}),
        ToolInvocation("code_x_v1_import_audit", {}),
    ], workspace=repo, user_message="code-x skill audit", max_steps=10)
    assert [item.status.value for item in result.results] == ["ok", "ok", "ok"]
    skill = result.results[0].data
    assert len(skill["tool_usage_cards"]) >= 12
    assert "fix" in skill["command_shortcuts"]
    assert skill["phase_to_next_action"]["validation_failed"]["next_tool"] == "failure_attribution_analyzer"
    audit = result.results[-1].data
    assert audit["code_x_essential_semantics_imported"] is True
    assert audit["all_v1_tools_imported"] is False


def test_codex_planbridge_skill_and_fix_trigger(tmp_path: Path) -> None:
    repo = _sample_repo(tmp_path)
    runtime = RuntimeEntry()
    skill = runtime.run_text("code-x skill bug_fix", workspace=repo, max_steps=3)
    assert skill.plan[0].tool_name == "code_x_skill_guide"
    assert skill.results[0].status.value == "ok"
    fix = runtime.run_text("code-x fix add function failure", workspace=repo, max_steps=10)
    assert [step.tool_name for step in fix.plan[:3]] == ["code_x_skill_guide", "project_rules_reader", "repo_map"]
    assert fix.results[0].status.value == "ok"
