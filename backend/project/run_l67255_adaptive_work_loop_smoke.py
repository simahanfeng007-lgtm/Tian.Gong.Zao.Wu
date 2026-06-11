"""L6.72.55 AdaptiveWorkLoop V1 smoke。

覆盖：
- compileall 失败后自动修复一次并复检；
- read_file missing 不乱自动创建，进入 failed_recoverable；
- pytest failure 构造 repair_context，repair 失败后 partial_with_resume；
- retry_budget 只用一次，不无限循环；
- TaskState 记录 original_plan / repair_plan / quality / next_action；
- repair 细节进入 workbench，不污染 conversation。 
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


if __name__ == "__main__" and os.environ.get("LINYUANZHE_RUN_FULL_SMOKE", "").strip().lower() not in {"1", "true", "yes", "on"}:
    print(json.dumps({
        "ok": True,
        "status": "SKIP",
        "smoke": "L6.72.55 AdaptiveWorkLoopV1",
        "reason": "heavy runtime smoke is opt-in to avoid no-output CI timeouts; set LINYUANZHE_RUN_FULL_SMOKE=1 to run the full scenario",
    }, ensure_ascii=False), flush=True)
    raise SystemExit(0)

# Full mode should remain package-read-only for Soul baseline state.
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")

from tiangong_agent_runtime.activation_protocol import ActivationForm
from tiangong_agent_runtime.frontend_contract import runtime_result_to_sse_events
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_mock import MockModelClient
from tiangong_agent_shell.model_client_port import ChatResult, ensure_compiled_prompt_envelope
from tiangong_agent_shell.tool_bridge import ToolExecutionMode


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def cfg() -> ModelConfig:
    return ModelConfig(
        provider="mock",
        base_url="",
        api_key="",
        model="mock-model",
        tool_execution_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode=PlannerMode.MODEL_SUGGEST,
    )


def work_form(work_type: str = "code") -> ActivationForm:
    return ActivationForm(
        mode="work",
        work_type=work_type,
        execution_depth="multi_step",
        tools_requested=True,
        required_tool_classes=("file_read", "file_write", "terminal_test"),
        risk_level="A3",
        need_quality_gate=True,
        need_user_confirm=False,
        expected_result="真实执行并返回 execution_report",
        final_output_contract="execution_report",
    )


class StaticPlanClient:
    provider = "mock"

    def __init__(self, plan: dict[str, Any], repair_plan: dict[str, Any] | None = None) -> None:
        self.plan = plan
        self.repair_plan = repair_plan or {"steps": []}
        self.phases: list[str] = []
        self.adaptive_calls = 0

    def chat(self, prompt: Any, config: ModelConfig) -> ChatResult:
        envelope = ensure_compiled_prompt_envelope(prompt)
        self.phases.append(envelope.phase)
        if envelope.phase == "adaptive_repair_plan":
            self.adaptive_calls += 1
            return ChatResult(json.dumps(self.repair_plan, ensure_ascii=False), provider=self.provider, model=config.model or "mock-model", raw={"prompt": envelope.public_dict()})
        return ChatResult(json.dumps(self.plan, ensure_ascii=False), provider=self.provider, model=config.model or "mock-model", raw={"prompt": envelope.public_dict()})


def _conversation_text(events: list[dict[str, Any]]) -> str:
    return "\n".join(str((event.get("payload") or {}).get("content") or "") for event in events if event.get("display_channel") == "conversation")


def _workbench_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event for event in events if event.get("display_channel") == "workbench"]


def test_compileall_auto_repair() -> None:
    with tempfile.TemporaryDirectory(prefix="l67255_compileall_") as tmp:
        root = Path(tmp)
        (root / "bad.py").write_text("def broken()\n    return 1\n", encoding="utf-8")
        runtime = RuntimeEntry()
        result = runtime.run_text(
            "检查项目 compileall 并修复",
            workspace=root,
            tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
            max_steps=8,
            planner_mode=PlannerMode.MODEL_SUGGEST,
            model_config=cfg(),
            model_client=MockModelClient(),
            activation_form=work_form("code"),
        )
        require(result.adaptive_work_loop is not None, "adaptive work loop should be attached")
        require(result.adaptive_work_loop.repair_attempted, "compileall failure should attempt repair")
        require(result.adaptive_work_loop.repair_executed, "compileall repair should execute")
        require(result.adaptive_work_loop.repair_succeeded, f"repair should succeed: {result.projection.summary}")
        require(result.status == "completed_pass" and result.projection.status == "completed_pass", "repair success status should be completed_pass")
        fixed = (root / "bad.py").read_text(encoding="utf-8")
        require("def broken():" in fixed, "compileall repair did not patch missing colon")
        repair_tools = [step.tool_name for step in result.adaptive_work_loop.repair_plan]
        require(repair_tools == ["document_apply_rewrite", "run_python_quality_check"], f"unexpected repair tools: {repair_tools}")
        task = runtime.task_state_ledger.latest_snapshot()["task"]
        require(task["status"] == "completed_pass", "TaskState should record completed_pass after repair")
        require(task["current_phase"] == "adaptive_repair_completed", "TaskState phase should show adaptive repair completed")
        history = task["plan_history"]
        require(any(item.get("kind") == "l6_72_55_adaptive_repair" and item.get("original_plan") and item.get("repair_plan") for item in history), "TaskState should record original_plan and repair_plan")
        require(task["quality_gate"] and task["next_action"] == "final_report", "TaskState should record quality and next_action")
        events = runtime_result_to_sse_events(result, run_id="run_l67255_compile", task_id=result.task_id)
        convo = _conversation_text(events)
        require("document_apply_rewrite" not in convo and "run_python_quality_check" not in convo, "conversation must not show repair tool details")
        require(any(((event.get("payload") or {}).get("adaptive_work_loop")) for event in _workbench_events(events) if event.get("event") == "execution_report"), "workbench execution_report should contain adaptive_work_loop details")


def test_read_file_missing_failed_recoverable() -> None:
    with tempfile.TemporaryDirectory(prefix="l67255_missing_") as tmp:
        client = StaticPlanClient({"steps": [{"tool_name": "read_file", "arguments": {"path": "missing_l67255.txt"}, "reason": "触发 missing file。"}]})
        runtime = RuntimeEntry()
        result = runtime.run_text(
            "读取 missing_l67255.txt",
            workspace=Path(tmp),
            tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
            max_steps=5,
            planner_mode=PlannerMode.MODEL_SUGGEST,
            model_config=cfg(),
            model_client=client,
            activation_form=work_form("file"),
        )
        require(result.adaptive_work_loop is not None and result.adaptive_work_loop.attempted, "missing read should create repair_context")
        require(not result.adaptive_work_loop.repair_executed, "read_file missing should not auto-create repair")
        require(result.status == "failed_recoverable" and result.projection.status == "failed_recoverable", f"unexpected missing status: {result.status}")
        require(result.adaptive_work_loop.repair_context.primary_failure_type == "tool_failed", "missing file should be classified as tool_failed")
        require(client.adaptive_calls == 0, "missing read should not spend repair planner call")


def test_pytest_failure_repair_context_and_partial() -> None:
    with tempfile.TemporaryDirectory(prefix="l67255_pytest_") as tmp:
        root = Path(tmp)
        (root / "test_bad.py").write_text("def test_bad():\n    assert 1 == 2\n", encoding="utf-8")
        client = StaticPlanClient(
            {"steps": [{"tool_name": "run_python_quality_check", "arguments": {"command": "pytest", "target": "."}, "reason": "运行 pytest。"}]},
            {"steps": [{"tool_name": "read_file", "arguments": {"path": "missing_after_pytest_failure.txt"}, "reason": "模拟 repair 失败。"}]},
        )
        runtime = RuntimeEntry()
        result = runtime.run_text(
            "运行 pytest 并在失败后修复一次",
            workspace=root,
            tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
            max_steps=6,
            planner_mode=PlannerMode.MODEL_SUGGEST,
            model_config=cfg(),
            model_client=client,
            activation_form=work_form("code"),
        )
        require(result.adaptive_work_loop is not None, "pytest failure should attach adaptive loop")
        adaptive = result.adaptive_work_loop
        require(adaptive.repair_attempted and adaptive.repair_executed, "pytest failure should attempt and execute repair plan")
        require(adaptive.repair_context.primary_failure_type == "validation_failed", "pytest should enter validation_failed repair_context")
        require(adaptive.status == "partial_with_resume" and result.status == "partial_with_resume", "failed repair should be partial_with_resume")
        require(client.adaptive_calls == 1, "AdaptiveWorkLoop V1 must call repair planner once only")
        require(adaptive.retry_budget_used == 1 and adaptive.retry_budget_max == 1, "retry budget should be exhausted after one repair attempt")
        require(adaptive.compiled_prompt_ids, "model repair plan must pass through PromptIntegrator envelope")
        task = runtime.task_state_ledger.latest_snapshot()["task"]
        require(task["retry_budget"]["used"] == 1, "TaskState should record retry budget used")
        require(task["status"] == "partial_with_resume", "TaskState should record partial_with_resume")
        events = runtime_result_to_sse_events(result, run_id="run_l67255_pytest", task_id=result.task_id)
        require("missing_after_pytest_failure" not in _conversation_text(events), "repair plan details must stay out of conversation")


def main() -> None:
    print("START L6.72.55 AdaptiveWorkLoopV1 full smoke", flush=True)
    test_compileall_auto_repair()
    print("PASS case compileall_auto_repair", flush=True)
    test_read_file_missing_failed_recoverable()
    print("PASS case read_file_missing_failed_recoverable", flush=True)
    test_pytest_failure_repair_context_and_partial()
    print("PASS case pytest_failure_repair_context_and_partial", flush=True)
    print("L6.72.55 AdaptiveWorkLoopV1 smoke PASS", flush=True)


if __name__ == "__main__":
    main()
