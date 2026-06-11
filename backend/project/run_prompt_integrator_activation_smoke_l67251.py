"""L6.72.51 PromptIntegrator-mediated Activation smoke.

验证目标：
- ProviderClient 拒绝裸 messages；
- ActivationForm 决策必须经过 PromptIntegrator envelope；
- work/file 可真实写盘并验真；
- chat 裁决不进入工具链；
- 文档系统不再抢占普通 txt 创建任务。
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PATH", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67251_prompt_integrator_soul_emotion_baseline.json"))
os.environ.setdefault("LINYUANZHE_STATE_DIR", str(Path(tempfile.mkdtemp(prefix="linyuanzhe_l67251_prompt_integrator_state_"))))
os.environ.setdefault("TIANGONG_STATE_DIR", os.environ["LINYUANZHE_STATE_DIR"])

from tiangong_agent_runtime.activation_form import ActivationFormDecider
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_mock import MockModelClient
from tiangong_agent_shell.prompt_compiler import compile_activation_decision_prompt
from tiangong_agent_shell.tool_bridge import ToolExecutionMode


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def config() -> ModelConfig:
    return ModelConfig(
        provider="mock",
        base_url="",
        api_key="",
        model="mock-model",
        tool_execution_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode=PlannerMode.MODEL_SUGGEST,
    )


def main() -> None:
    cfg = config()
    mock = MockModelClient()
    runtime = RuntimeEntry()

    # Provider boundary: raw messages are rejected.
    rejected = False
    try:
        mock.chat([{"role": "system", "content": "raw"}], cfg)  # type: ignore[arg-type]
    except TypeError:
        rejected = True
    require(rejected, "mock provider must reject raw messages")

    envelope = compile_activation_decision_prompt("创建 smoke.txt 内容 hello", config=cfg, user_selected_mode="chat")
    require(envelope.source == "PromptIntegrator" and envelope.compiled_prompt_id, "activation prompt must be compiled envelope")
    activation = ActivationFormDecider().decide(
        "创建 smoke_l67251.txt 内容 hello_l67251",
        model_config=cfg,
        model_client=mock,
        user_selected_mode="chat",
        max_steps=8,
    )
    require(activation.ok and activation.form is not None, "activation decider failed")
    require(activation.form.mode == "work" and activation.form.tools_requested, "LLM should fill work for execution request")

    with tempfile.TemporaryDirectory(prefix="l67251_activation_") as tmp:
        root = Path(tmp)
        result = runtime.run_text(
            "创建 smoke_l67251.txt 内容 hello_l67251",
            workspace=root,
            tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
            max_steps=8,
            planner_mode=PlannerMode.MODEL_SUGGEST,
            model_config=cfg,
            model_client=mock,
            activation_form=activation.form,
        )
        require(result.projection.status == "ok", f"work execution failed: {result.projection.summary}")
        target = root / "smoke_l67251.txt"
        require(target.exists(), "write_workspace_file did not create file")
        require(target.read_text(encoding="utf-8") == "hello_l67251", "created file content mismatch")
        require(result.planner_result is not None, "planner result must be present for executed work")

        model_prompt = "模型规划 smoke：检查项目并输出总结"
        model_activation = ActivationFormDecider().decide(model_prompt, model_config=cfg, model_client=mock, user_selected_mode="chat", max_steps=8)
        require(model_activation.ok and model_activation.form is not None, "model-plan activation failed")
        model_result = runtime.run_text(
            model_prompt,
            workspace=root,
            tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
            max_steps=4,
            planner_mode=PlannerMode.MODEL_SUGGEST,
            model_config=cfg,
            model_client=mock,
            activation_form=model_activation.form,
        )
        require(model_result.planner_result is not None and model_result.planner_result.compiled_prompt_ids, "model planner must record compiled prompt ids")

        chat_activation = ActivationFormDecider().decide("你好", model_config=cfg, model_client=mock, user_selected_mode="chat")
        require(chat_activation.ok and chat_activation.form is not None, "chat activation failed")
        require(chat_activation.form.mode == "chat" and not chat_activation.form.tools_requested, "chat should not request tools")
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
        require(not chat_result.has_plan, "chat ActivationForm must not create tool plan")

    plan = PlanBridge().build_plan("创建 ordinary.txt 内容 hello")
    require(not plan or all(step.tool_name not in {"document_parse", "document_rewrite_plan"} for step in plan), "ordinary txt creation must not be hijacked by document tools")

    print("L6.72.51 prompt_integrator_activation_smoke PASS")


if __name__ == "__main__":
    main()
