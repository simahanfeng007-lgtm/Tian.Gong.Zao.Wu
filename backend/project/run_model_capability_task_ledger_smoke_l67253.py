"""L6.72.53 被动模型画像与任务状态账本 smoke。

验证目标：
- ModelCapabilityAdapter 能为常见 provider/model 生成画像与策略；
- ModelProfileStore 只写安全元数据，不写 API Key；
- Runtime.run_text 不改变原工作执行效果，同时生成 task_state 账本；
- 前端无需变更，真实工具落盘路径仍由 Runtime 执行。
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

from tiangong_agent_runtime.activation_form import ActivationFormDecider
from tiangong_agent_runtime.model_capability_adapter import ModelCapabilityAdapter
from tiangong_agent_runtime.model_profile_store import ModelProfileStore
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_mock import MockModelClient
from tiangong_agent_shell.tool_bridge import ToolExecutionMode


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def config() -> ModelConfig:
    return ModelConfig(
        provider="mock",
        base_url="",
        api_key="SECRET_SHOULD_NOT_BE_WRITTEN",
        model="mock-model",
        tool_execution_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode=PlannerMode.MODEL_SUGGEST,
    )


def main() -> None:
    adapter = ModelCapabilityAdapter()
    deepseek = adapter.resolve_profile(SimpleNamespace(provider="deepseek", model="deepseek-v4-pro", api_key="SHOULD_NOT_APPEAR"))
    openai = adapter.resolve_profile(SimpleNamespace(provider="openai", model="gpt-4.1", api_key="SHOULD_NOT_APPEAR"))
    qwen = adapter.resolve_profile(SimpleNamespace(provider="qwen", model="qwen-plus", api_key="SHOULD_NOT_APPEAR"))
    require(deepseek.recommended_role in {"main_brain_guarded", "main_brain_full"}, "deepseek role not resolved")
    require(openai.recommended_role == "main_brain_full", "openai strong model role mismatch")
    require(qwen.recommended_role == "micro_planner", "qwen should be guarded micro planner")
    policy = adapter.resolve_policy(deepseek)
    require(policy.passive_only is True, "L6.72.53 policy must be passive by default")
    require(policy.max_plan_steps_per_round >= 3, "policy max steps too low for guarded model")

    old_soul_path = os.environ.get("TIANGONG_SOUL_BASELINE_PATH")
    old_soul_persist = os.environ.get("TIANGONG_SOUL_BASELINE_PERSIST")
    with tempfile.TemporaryDirectory(prefix="l67253_model_ledger_") as tmp:
        root = Path(tmp)
        os.environ["TIANGONG_SOUL_BASELINE_PATH"] = str(root / ".linyuanzhe" / "soul" / "soul_emotion_baseline.json")
        os.environ["TIANGONG_SOUL_BASELINE_PERSIST"] = "1"
        store = ModelProfileStore()
        profile_ref = store.save(root, deepseek, policy)
        require(profile_ref and Path(profile_ref).exists(), "profile store did not write file")
        raw_profile = Path(profile_ref).read_text(encoding="utf-8")
        require("SHOULD_NOT_APPEAR" not in raw_profile and "SECRET" not in raw_profile, "profile store leaked api key")

        cfg = config()
        mock = MockModelClient()
        runtime = RuntimeEntry()
        activation = ActivationFormDecider().decide(
            "创建 smoke_l67253.txt 内容 hello_l67253",
            model_config=cfg,
            model_client=mock,
            user_selected_mode="work",
            max_steps=8,
        )
        require(activation.ok and activation.form is not None, "activation failed")
        result = runtime.run_text(
            "创建 smoke_l67253.txt 内容 hello_l67253",
            workspace=root,
            tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
            max_steps=8,
            planner_mode=PlannerMode.MODEL_SUGGEST,
            model_config=cfg,
            model_client=mock,
            activation_form=activation.form,
        )
        require(result.projection.status == "ok", f"work execution failed: {result.projection.summary}")
        target = root / "smoke_l67253.txt"
        require(target.exists(), "write_workspace_file did not create target")
        require(target.read_text(encoding="utf-8") == "hello_l67253", "target content mismatch")
        require(result.task_id.startswith("task_"), "RuntimeRunResult must expose passive task_id")
        require(result.model_profile is not None and result.model_execution_policy is not None, "model profile/policy missing from result")
        require(result.model_execution_policy.passive_only is True, "policy unexpectedly active")
        task_path = root / ".linyuanzhe" / "tasks" / result.task_id / "task_state.json"
        events_path = root / ".linyuanzhe" / "tasks" / result.task_id / "events.jsonl"
        require(task_path.exists(), "task_state.json not written")
        require(events_path.exists(), "events.jsonl not written")
        task = json.loads(task_path.read_text(encoding="utf-8"))
        require(task["status"] == "completed_pass", f"task status mismatch: {task['status']}")
        require(task["activation_form"]["mode"] == "work", "activation form not recorded")
        require(task["model_profile"]["passive_only"] is True, "model profile must be passive")
        require(any(step["tool_name"] == "write_workspace_file" for step in task["executed_steps"]), "executed write step not recorded")
        raw_task = task_path.read_text(encoding="utf-8") + events_path.read_text(encoding="utf-8")
        require("SECRET_SHOULD_NOT_BE_WRITTEN" not in raw_task, "task ledger leaked api key")

        chat_activation = ActivationFormDecider().decide("你好", model_config=cfg, model_client=mock, user_selected_mode="chat")
        require(chat_activation.ok and chat_activation.form is not None, "chat activation failed")
        chat_result = runtime.run_text(
            "你好",
            workspace=root,
            tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
            max_steps=4,
            planner_mode=PlannerMode.MODEL_SUGGEST,
            model_config=cfg,
            model_client=mock,
            activation_form=chat_activation.form,
        )
        require(not chat_result.has_plan, "chat activation should not create a tool plan")
        require(chat_result.task_id.startswith("task_"), "chat/no-tool run should still be safely ledgered")

    if old_soul_path is None:
        os.environ.pop("TIANGONG_SOUL_BASELINE_PATH", None)
    else:
        os.environ["TIANGONG_SOUL_BASELINE_PATH"] = old_soul_path
    if old_soul_persist is None:
        os.environ.pop("TIANGONG_SOUL_BASELINE_PERSIST", None)
    else:
        os.environ["TIANGONG_SOUL_BASELINE_PERSIST"] = old_soul_persist
    print("L6.72.53 model_capability_task_ledger_smoke PASS")


if __name__ == "__main__":
    main()
