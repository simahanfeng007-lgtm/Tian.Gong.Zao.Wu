"""L6.72.54 work 模式禁止静默退回 chat smoke。"""

from __future__ import annotations

import os
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PATH", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67254_soul_emotion_baseline.json"))
os.environ.setdefault("LINYUANZHE_STATE_DIR", str(Path(tempfile.mkdtemp(prefix="linyuanzhe_l67254_state_"))))
os.environ.setdefault("TIANGONG_STATE_DIR", os.environ["LINYUANZHE_STATE_DIR"])

from tiangong_agent_runtime.activation_protocol import ActivationForm  # noqa: E402
from tiangong_agent_runtime.frontend_contract import runtime_result_to_sse_events  # noqa: E402
from tiangong_agent_runtime.planner_mode import PlannerMode  # noqa: E402
from tiangong_agent_runtime.runtime_entry import RuntimeEntry  # noqa: E402
from tiangong_agent_shell.config_loader import ModelConfig  # noqa: E402
from tiangong_agent_shell.model_client_port import ChatResult, ensure_compiled_prompt_envelope  # noqa: E402


class InvalidJsonThenRepairClient:
    provider = "mock"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def chat(self, prompt, config: ModelConfig) -> ChatResult:  # type: ignore[override]
        envelope = ensure_compiled_prompt_envelope(prompt)
        self.calls.append(envelope.phase)
        if envelope.phase == "activation_decision":
            return ChatResult(
                content=json.dumps(
                    {
                        "mode": "work",
                        "work_type": "file",
                        "execution_depth": "single_step",
                        "tools_requested": True,
                        "required_tool_classes": ["file_read"],
                        "risk_level": "A1",
                        "need_quality_gate": False,
                        "need_user_confirm": False,
                        "expected_result": "列目录",
                        "final_output_contract": "execution_report",
                        "reason": "smoke",
                    },
                    ensure_ascii=False,
                ),
                provider="mock",
                model=config.model or "mock-model",
            )
        if envelope.phase == "planner_execution":
            return ChatResult(content="这不是合法 JSON plan，但应该进入 plan_repair。", provider="mock", model=config.model or "mock-model")
        if envelope.phase == "planner_repair":
            return ChatResult(content=json.dumps({"steps": [{"tool_name": "list_dir", "arguments": {"path": "."}, "reason": "repair smoke"}]}, ensure_ascii=False), provider="mock", model=config.model or "mock-model")
        return ChatResult(content="{}", provider="mock", model=config.model or "mock-model")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    os.environ["TIANGONG_ALLOW_INTERNAL_MOCK"] = "1"
    workspace = Path(tempfile.mkdtemp(prefix="l67254_work_smoke_"))
    unavailable = ModelConfig(provider="openai_compatible", base_url="", api_key="", model="")
    ready_mock = ModelConfig(provider="mock", base_url="", api_key="", model="mock-model")
    runtime = RuntimeEntry()

    # 1. work + Provider 不可用 + 明确创建 txt：走确定性回退并真实落盘。
    result = runtime.run_text(
        "创建 l67254_fallback.txt 内容 hello_l67254",
        workspace=workspace,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=unavailable,
        model_client=None,
    )
    assert_true(result.final_output_contract == "execution_report", "work output contract must be execution_report")
    assert_true(result.deterministic_fallback_used, "deterministic fallback must be marked")
    assert_true(result.projection.status == "deterministic_fallback", "projection status must show deterministic_fallback")
    assert_true((workspace / "l67254_fallback.txt").read_text(encoding="utf-8") == "hello_l67254", "fallback write must be physically verified")
    assert_true(result.has_executed_tools, "fallback must execute tool")

    # 2. work + Provider 不可用 + 复杂代码修复：不得假装完成，不得退回聊天。
    complex_result = runtime.run_text(
        "修复这个项目的跨文件代码错误并跑 pytest",
        workspace=workspace,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=unavailable,
        model_client=None,
    )
    assert_true(not complex_result.has_plan, "complex unavailable provider task must not have fake plan")
    assert_true(complex_result.projection.status in {"provider_not_ready", "model_required", "failed_recoverable"}, "complex unavailable provider task must produce work failure status")
    assert_true(complex_result.final_output_contract == "execution_report", "complex failure still must be execution_report")
    assert_true("Provider" in complex_result.projection.summary or "模型" in complex_result.projection.summary, "provider_not_ready summary must be user visible")

    # 3. invalid JSON 进入 plan_repair，修复后继续执行。
    repair_client = InvalidJsonThenRepairClient()
    repair_result = RuntimeEntry().run_text(
        "模型规划 smoke：请根据上下文决定需要的工具并列出当前目录",
        workspace=workspace,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=ready_mock,
        model_client=repair_client,
    )
    assert_true(repair_result.has_plan, "plan_repair success must produce a plan")
    assert_true(repair_result.plan_repair_attempted, "plan_repair_attempted must be true")
    assert_true("planner_repair" in repair_client.calls, "repair prompt must go through PromptIntegrator envelope")
    assert_true(repair_result.projection.status in {"ok", "completed_pass"}, "repaired list_dir plan should execute")

    # 4. A5 不执行、不回退聊天。
    a5_form = ActivationForm(mode="work", work_type="terminal", execution_depth="single_step", tools_requested=True, required_tool_classes=("terminal",), risk_level="A5", need_quality_gate=True, need_user_confirm=True, final_output_contract="execution_report")
    a5_result = RuntimeEntry().run_text(
        "执行高危不可逆操作",
        workspace=workspace,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=ready_mock,
        model_client=repair_client,
        activation_form=a5_form,
    )
    assert_true(not a5_result.has_executed_tools, "A5 must not execute tools")
    assert_true(a5_result.projection.status in {"blocked_A5", "awaiting_confirmation", "failed_recoverable"}, "A5 must be blocked or confirmation-gated")

    # 5. TaskState 写入 failure_kind/status/next_action。
    task_state_root = Path(os.environ.get("LINYUANZHE_STATE_DIR") or os.environ.get("TIANGONG_STATE_DIR") or (workspace / ".linyuanzhe"))
    task_state_files = list((task_state_root / "tasks").glob("*/task_state.json"))
    assert_true(bool(task_state_files), "TaskState task_state.json must be written")
    failure_snapshots = [json.loads(path.read_text(encoding="utf-8")) for path in task_state_files]
    assert_true(any(item.get("status") in {"provider_not_ready", "failed_recoverable", "blocked_A5", "deterministic_fallback"} for item in failure_snapshots), "TaskState must contain active work status")
    assert_true(any(item.get("next_action") for item in failure_snapshots), "TaskState must contain next_action")

    # 6. SSE 投影必须带 display_channel，conversation 只给简明 final。
    events = runtime_result_to_sse_events(result, run_id="run_l67254", task_id=result.task_id)
    assert_true(all(e.get("display_channel") for e in events), "SSE events must carry display_channel")
    assert_true(any(e["event"] == "execution_report" and e["display_channel"] == "workbench" for e in events), "full execution report must go to workbench")
    finals = [e for e in events if e["event"] == "assistant_final"]
    assert_true(finals and finals[0]["display_channel"] == "conversation", "assistant_final must be conversation")
    assert_true("write_workspace_file" not in str(finals[0].get("payload", {})), "conversation final must not include tool workflow details")

    source = Path("backend/project/tiangong_agent_shell/cli_loop.py").read_text(encoding="utf-8") if Path("backend/project/tiangong_agent_shell/cli_loop.py").exists() else Path("tiangong_agent_shell/cli_loop.py").read_text(encoding="utf-8")
    assert_true("activation_form.mode == \"chat\"" not in source, "CLI must not fallback from work activation chat to run_chat_once")
    print("PASS L6.72.54 no silent chat fallback smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
