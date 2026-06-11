"""L6.72.57 SkillPlaybookRouter smoke。"""

from __future__ import annotations

import os
import json
import tempfile
from pathlib import Path
from typing import Any

os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PATH", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67257_soul_emotion_baseline.json"))
os.environ.setdefault("LINYUANZHE_STATE_DIR", str(Path(tempfile.mkdtemp(prefix="linyuanzhe_l67257_state_"))))
os.environ.setdefault("TIANGONG_STATE_DIR", os.environ["LINYUANZHE_STATE_DIR"])

from tiangong_agent_runtime.activation_protocol import ActivationForm
from tiangong_agent_runtime.frontend_contract import runtime_result_to_sse_events
from tiangong_agent_runtime.model_capability_adapter import ModelCapabilityAdapter
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.skill_playbook_router import SkillPlaybookRouter
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_mock import MockModelClient
from tiangong_agent_shell.tool_bridge import ToolExecutionMode


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def cfg(provider: str = "mock", model: str = "mock-model") -> ModelConfig:
    return ModelConfig(provider=provider, base_url="", api_key="", model=model, tool_execution_mode=ToolExecutionMode.RUNTIME_GOVERNED, planner_mode=PlannerMode.MODEL_SUGGEST)


def work_form(work_type: str = "mixed") -> ActivationForm:
    return ActivationForm(mode="work", work_type=work_type, execution_depth="multi_step", tools_requested=True, required_tool_classes=("file_read", "file_write", "terminal_test"), risk_level="A3", need_quality_gate=True, need_user_confirm=False, expected_result="真实执行并返回 execution_report", final_output_contract="execution_report")


def _conversation_text(events: list[dict[str, Any]]) -> str:
    return "\n".join(str((event.get("payload") or {}).get("content") or "") for event in events if event.get("display_channel") == "conversation")


def _workbench_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event for event in events if event.get("display_channel") == "workbench"]


def _route(goal: str, work_type: str = "mixed", learned_assets: list[str] | None = None):
    runtime = RuntimeEntry()
    adapter = ModelCapabilityAdapter()
    profile = adapter.resolve_profile(cfg(provider="deepseek", model="deepseek-v4-pro"))
    return SkillPlaybookRouter().route(activation_form=work_form(work_type), user_goal=goal, model_profile=profile, available_tools=runtime.available_tools(), learned_assets=learned_assets or [])


def test_code_x_bug_fix_default() -> None:
    route = _route("修复这个项目的跨文件 Python 错误并跑 pytest", "code")
    require(route.playbook_id == "code_x_bug_fix", f"code repair should route to code_x_bug_fix: {route.public_dict()}")
    phases = set(route.phase_sequence)
    for phase in ("repo_discovery", "localization", "patch_planning", "validation", "repair", "delivery"):
        require(phase in phases, f"missing code phase: {phase}")
    require("scan_project" in route.recommended_tools and "run_python_quality_check" in route.recommended_tools, "code route should recommend project scan and quality check")
    require("document_parse" in route.forbidden_tools, "code route should forbid document_parse by default")


def test_txt_file_not_document_parse() -> None:
    route = _route("创建 hello.txt 内容 abc 并验证", "file")
    require(route.playbook_id == "workspace_file_simple", f"txt task should route to workspace_file_simple: {route.public_dict()}")
    require("write_workspace_file" in route.recommended_tools and "read_file" in route.recommended_tools, "file route should recommend write/read")
    require("document_parse" in route.forbidden_tools and "document_apply_rewrite" in route.forbidden_tools, "file route should forbid document tools")


def test_document_task_route() -> None:
    route = _route("解析 report.docx 并导出摘要", "document")
    require(route.playbook_id == "document_parse_rewrite", f"docx task should route to document_parse_rewrite: {route.public_dict()}")
    for tool in ("document_parse", "document_query", "document_rewrite_plan", "document_apply_rewrite", "document_export"):
        require(tool in route.recommended_tools, f"document route missing {tool}")


def test_delivery_route() -> None:
    route = _route("扫描项目并打包交付 zip release", "mixed")
    require(route.playbook_id == "delivery_package", f"delivery task should route to delivery_package: {route.public_dict()}")
    require("scan_project" in route.recommended_tools and "create_zip_package" in route.recommended_tools, "delivery route should recommend scan/package")


def test_learned_assets_candidate_only() -> None:
    route = _route("修复项目", "code", learned_assets=["learned_magic_patch", "normal_tool"])
    require("learned_magic_patch" in route.learned_asset_candidates, "learned assets should be surfaced as candidates")
    require("learned_magic_patch" not in route.recommended_tools, "learned assets must not hijack recommended_tools by default")
    require(route.public_dict()["execution_boundary"]["learned_assets_candidate_only"], "route must declare learned candidate boundary")


def test_runtime_projection_and_taskstate() -> None:
    with tempfile.TemporaryDirectory(prefix="l67257_runtime_") as tmp:
        root = Path(tmp)
        runtime = RuntimeEntry()
        result = runtime.run_text("修复这个项目并跑 compileall", workspace=root, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED, max_steps=8, planner_mode=PlannerMode.MODEL_SUGGEST, model_config=cfg(), model_client=MockModelClient(), activation_form=work_form("code"))
        require(result.skill_playbook_route is not None, "RuntimeRunResult should expose skill_playbook_route")
        require(result.skill_playbook_route.playbook_id == "code_x_bug_fix", "runtime should route code task to code_x_bug_fix")
        task = runtime.task_state_ledger.latest_snapshot()["task"]
        require(task.get("playbook_routes"), "TaskState should record playbook_routes")
        require(task["playbook_routes"][-1]["playbook_id"] == "code_x_bug_fix", "TaskState should persist code_x route")
        events = runtime_result_to_sse_events(result, run_id="run_l67257", task_id=result.task_id)
        convo = _conversation_text(events)
        require("code_x_bug_fix" not in convo and "repo_discovery" not in convo and "patch_planning" not in convo, "conversation must not show playbook internals")
        reports = [event for event in _workbench_events(events) if event.get("event") == "execution_report"]
        require(reports, "workbench should have execution_report")
        payload = reports[-1].get("payload") or {}
        require(payload.get("skill_playbook_route"), "workbench execution_report should carry skill_playbook_route")
        require(payload.get("context_window_bundle"), "workbench execution_report should keep context_window_bundle")


def main() -> int:
    test_code_x_bug_fix_default()
    test_txt_file_not_document_parse()
    test_document_task_route()
    test_delivery_route()
    test_learned_assets_candidate_only()
    test_runtime_projection_and_taskstate()
    print("L6.72.57 SkillPlaybookRouter smoke PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
