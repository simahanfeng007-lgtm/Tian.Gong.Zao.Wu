from __future__ import annotations

import os
import json
import tempfile
from pathlib import Path
from typing import Any

os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PATH", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67256_soul_emotion_baseline.json"))
os.environ.setdefault("LINYUANZHE_STATE_DIR", str(Path(tempfile.mkdtemp(prefix="linyuanzhe_l67256_state_"))))
os.environ.setdefault("TIANGONG_STATE_DIR", os.environ["LINYUANZHE_STATE_DIR"])

from tiangong_agent_runtime.activation_protocol import ActivationForm
from tiangong_agent_runtime.context_window_manager import ContextWindowManager
from tiangong_agent_runtime.frontend_contract import runtime_result_to_sse_events
from tiangong_agent_runtime.model_capability_adapter import ModelCapabilityAdapter
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.task_state_schema import TaskState, now_iso
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.errors import ModelClientError
from tiangong_agent_shell.model_client_port import ChatResult, ensure_compiled_prompt_envelope
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

SECRET = "MOCK_RAW_PROVIDER_SECRET_FOR_REDACTION"
TOKEN = "mytoken1234567890"
BASE = "https://private.example/api"
RAW_PROMPT_SENTINEL = "RAW_PROMPT_SENTINEL_SHOULD_NOT_LEAK"


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def cfg(provider: str = "mock", model: str = "mock-model", api_key: str = "") -> ModelConfig:
    return ModelConfig(provider=provider, base_url="", api_key=api_key, model=model, tool_execution_mode=ToolExecutionMode.RUNTIME_GOVERNED, planner_mode=PlannerMode.MODEL_SUGGEST)


def work_form(work_type: str = "file") -> ActivationForm:
    return ActivationForm(mode="work", work_type=work_type, execution_depth="multi_step", tools_requested=True, required_tool_classes=("file_read", "file_write", "terminal_test"), risk_level="A3", need_quality_gate=True, need_user_confirm=False, expected_result="真实执行并返回 execution_report", final_output_contract="execution_report")


def _pack(bundle: Any, name: str) -> dict[str, Any]:
    for item in bundle.public_dict().get("packs", []):
        if item.get("name") == name:
            return item.get("payload") or {}
    return {}


def _conversation_text(events: list[dict[str, Any]]) -> str:
    return "\n".join(str((event.get("payload") or {}).get("content") or "") for event in events if event.get("display_channel") == "conversation")


def _workbench_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event for event in events if event.get("display_channel") == "workbench"]


def test_b_tier_short_context() -> None:
    adapter = ModelCapabilityAdapter()
    runtime = RuntimeEntry()
    profile = adapter.resolve_profile(cfg(provider="qwen", model="qwen-max"))
    policy = adapter.resolve_policy(profile)
    bundle = ContextWindowManager().build_context_pack(user_goal="长链修复任务：" + "目标" * 3000, model_profile=profile, model_policy=policy, stage="planning", available_tools=runtime.available_tools(), external_context_hint=f"api_key={SECRET} token={TOKEN} base_url={BASE} {RAW_PROMPT_SENTINEL} " + "上下文" * 3000)
    require(bundle.model_tier == "B", f"qwen should be B/micro planner, got {bundle.model_tier}")
    require("EvidencePack" not in bundle.pack_names and "PlaybookPack" not in bundle.pack_names, "B tier must not receive full evidence/playbook")
    tools = _pack(bundle, "ToolPack").get("candidate_tools") or []
    require(len(tools) <= 5, f"B tier should receive at most 5 candidate tools, got {len(tools)}")
    card = bundle.prompt_card()
    require(len(card) <= bundle.max_context_chars, "B prompt card must stay within context budget")
    require(SECRET not in card and TOKEN not in card and BASE not in card, "short context must redact secrets/endpoints")


def test_s_tier_full_context_and_playbook() -> None:
    adapter = ModelCapabilityAdapter()
    runtime = RuntimeEntry()
    profile = adapter.resolve_profile(cfg(provider="openai", model="gpt-5.5-pro"))
    policy = adapter.resolve_policy(profile)
    now = now_iso()
    task = TaskState(task_id="task_ctx_s", created_at=now, updated_at=now, user_goal="修复这个 Python 项目并打包交付", current_phase="repo_discovery", status="planning", next_action="build_code_x_plan")
    task.evidence_refs.append({"path": "src/app.py", "hash": "abc123", "summary": "导入错误定位证据"})
    bundle = ContextWindowManager().build_context_pack(user_goal=task.user_goal, model_profile=profile, model_policy=policy, task_state=task, stage="planning", activation_form=work_form("code"), available_tools=runtime.available_tools())
    require(bundle.model_tier == "S", f"openai/gpt should be S/full, got {bundle.model_tier}")
    require("EvidencePack" in bundle.pack_names and "PlaybookPack" in bundle.pack_names, "S tier must receive evidence/playbook")
    require(len(_pack(bundle, "ToolPack").get("candidate_tools") or []) > 5, "S tier should receive richer tool candidates")


def test_long_chain_state_retention() -> None:
    adapter = ModelCapabilityAdapter()
    profile = adapter.resolve_profile(cfg(provider="deepseek", model="deepseek-v4-pro"))
    policy = adapter.resolve_policy(profile)
    now = now_iso()
    task = TaskState(task_id="task_ctx_long", created_at=now, updated_at=now, user_goal="修复项目并完成最终验证", current_phase="validation", status="partial_with_resume", next_action="resume_validation")
    task.executed_steps = [{"step_id": f"step_{i}", "tool_name": "list_dir", "status": "ok", "summary": f"step {i} ok"} for i in range(25)]
    card = ContextWindowManager().build_context_pack(user_goal=task.user_goal, model_profile=profile, model_policy=policy, task_state=task, stage="validation", activation_form=work_form("code"), current_plan=[]).prompt_card()
    require("修复项目" in card and "validation" in card and "resume_validation" in card and "25" in card, "context pack must retain long-chain goal/phase/next_action/count")


def test_no_secret_raw_prompt_or_full_sensitive_body_leak() -> None:
    adapter = ModelCapabilityAdapter()
    profile = adapter.resolve_profile(cfg(provider="openai", model="gpt-5.5-pro"))
    policy = adapter.resolve_policy(profile)
    bundle = ContextWindowManager().build_context_pack(user_goal=f"创建报告。api_key={SECRET} token={TOKEN} raw_prompt={RAW_PROMPT_SENTINEL}", model_profile=profile, model_policy=policy, stage="planning", external_context_hint=f"base_url={BASE}\napi_key={SECRET}\ntoken={TOKEN}\nraw_prompt={RAW_PROMPT_SENTINEL}\n" + "FULL_SENSITIVE_BODY_" * 500)
    material = bundle.prompt_card() + json.dumps(bundle.public_dict(), ensure_ascii=False)
    for raw in (SECRET, TOKEN, BASE, RAW_PROMPT_SENTINEL):
        require(raw not in material, f"context bundle leaked sensitive/raw material: {raw}")
    require(material.count("FULL_SENSITIVE_BODY_") < 5, "context bundle should not keep full sensitive body")


class OverflowOnceClient:
    provider = "mock"
    def __init__(self) -> None:
        self.phases: list[str] = []
        self.raised = False
    def chat(self, prompt: Any, config: ModelConfig) -> ChatResult:
        envelope = ensure_compiled_prompt_envelope(prompt)
        self.phases.append(envelope.phase)
        if envelope.phase == "planner_execution" and not self.raised:
            self.raised = True
            raise ModelClientError("context_overflow: too many tokens", detail="context length exceeded / maximum context")
        if envelope.phase == "planner_execution_context_retry":
            return ChatResult(json.dumps({"steps": [{"tool_name": "list_dir", "arguments": {"path": "."}, "reason": "压缩上下文后重试目录读取。"}]}, ensure_ascii=False), provider=self.provider, model=config.model or "mock-model")
        return ChatResult(json.dumps({"steps": [{"tool_name": "list_dir", "arguments": {"path": "."}, "reason": "默认计划。"}]}, ensure_ascii=False), provider=self.provider, model=config.model or "mock-model")


def test_context_overflow_compact_retry_and_projection() -> None:
    with tempfile.TemporaryDirectory(prefix="l67256_overflow_") as tmp:
        runtime = RuntimeEntry()
        client = OverflowOnceClient()
        result = runtime.run_text("列出当前目录", workspace=Path(tmp), tool_mode=ToolExecutionMode.RUNTIME_GOVERNED, max_steps=8, planner_mode=PlannerMode.MODEL_SUGGEST, model_config=cfg(), model_client=client, external_context_hint="超长上下文 " * 6000, activation_form=work_form("file"))
        require(result.has_plan, "context overflow retry should still produce plan")
        require("planner_execution_context_retry" in client.phases, f"planner should retry with compact context, phases={client.phases}")
        require(result.planner_result is not None and result.planner_result.repair_attempted, "planner_result should mark context retry attempted")
        snapshot = runtime.task_state_ledger.latest_snapshot()["task"]
        require(snapshot.get("context_packs"), "TaskState should record context_packs summary")
        events = runtime_result_to_sse_events(result, run_id="run_l67256", task_id=result.task_id)
        require("ContextWindowManager" not in _conversation_text(events), "context pack details must not enter conversation")
        reports = [event for event in _workbench_events(events) if event.get("event") == "execution_report"]
        require(reports and (reports[-1].get("payload") or {}).get("context_window_bundle"), "workbench execution_report should carry context_window_bundle")


def main() -> int:
    test_b_tier_short_context()
    test_s_tier_full_context_and_playbook()
    test_long_chain_state_retention()
    test_no_secret_raw_prompt_or_full_sensitive_body_leak()
    test_context_overflow_compact_retry_and_projection()
    print("L6.72.56 ContextWindowManager smoke PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
