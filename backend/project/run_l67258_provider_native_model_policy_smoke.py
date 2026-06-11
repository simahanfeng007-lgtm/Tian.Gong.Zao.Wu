"""L6.72.58 Provider Native Adapter + 主动 ModelPolicy smoke。"""

from __future__ import annotations

import os
import json
import tempfile
from pathlib import Path
from typing import Any

os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PATH", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67258_soul_emotion_baseline.json"))
os.environ.setdefault("LINYUANZHE_STATE_DIR", str(Path(tempfile.mkdtemp(prefix="linyuanzhe_l67258_state_"))))
os.environ.setdefault("TIANGONG_STATE_DIR", os.environ["LINYUANZHE_STATE_DIR"])

from tiangong_agent_runtime.activation_protocol import ActivationForm
from tiangong_agent_runtime.frontend_contract import runtime_result_to_sse_events
from tiangong_agent_runtime.model_capability_adapter import ModelCapabilityAdapter
from tiangong_agent_runtime.model_execution_policy_engine import ModelExecutionPolicyEngine
from tiangong_agent_runtime.model_planner import ModelPlanner
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_shell.composition_root import select_model_client
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.errors import ModelClientError
from tiangong_agent_shell.model_client_port import ChatResult, CompiledPromptEnvelope
from tiangong_agent_shell.prompt_compiler import provider_is_ready
from tiangong_agent_shell.providers.anthropic_adapter import AnthropicNativeAdapter
from tiangong_agent_shell.providers.gemini_adapter import GeminiNativeAdapter
from tiangong_agent_shell.providers.openai_adapter import OpenAINativeAdapter
from tiangong_agent_shell.providers.openai_compatible_adapter import OpenAICompatibleAdapter
from tiangong_agent_shell.providers.provider_error import ProviderErrorKind, classify_provider_error


class StaticPlanClient:
    provider = "mock"

    def __init__(self, plan: dict[str, Any]) -> None:
        self.plan = plan
        self.calls: list[CompiledPromptEnvelope] = []

    def chat(self, prompt: CompiledPromptEnvelope, config: ModelConfig) -> ChatResult:
        self.calls.append(prompt)
        return ChatResult(content=json.dumps(self.plan, ensure_ascii=False), provider="mock", model=config.model)


class FailIfCalledClient:
    provider = "mock"

    def chat(self, prompt: CompiledPromptEnvelope, config: ModelConfig) -> ChatResult:  # pragma: no cover - should never be called
        raise AssertionError("弱模型被错误送入主脑 Planner。")


class ContextOverflowThenOkClient:
    provider = "mock"

    def __init__(self) -> None:
        self.calls: list[CompiledPromptEnvelope] = []

    def chat(self, prompt: CompiledPromptEnvelope, config: ModelConfig) -> ChatResult:
        self.calls.append(prompt)
        if len(self.calls) == 1:
            raise ModelClientError("Provider 上下文超限", detail="context_overflow: maximum context length exceeded", error_kind="context_overflow", provider="openai", retryable=False)
        plan = {"steps": [{"tool_name": "list_dir", "arguments": {"path": "."}, "reason": "context compact retry ok"}]}
        return ChatResult(content=json.dumps(plan, ensure_ascii=False), provider="mock", model=config.model)


class TimeoutClient:
    provider = "mock"

    def chat(self, prompt: CompiledPromptEnvelope, config: ModelConfig) -> ChatResult:
        raise ModelClientError("Provider 请求超时", detail="timed out after 60s", error_kind="timeout", provider="openai", retryable=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def work_form(work_type: str = "file", depth: str = "multi_step") -> ActivationForm:
    return ActivationForm(mode="work", work_type=work_type, execution_depth=depth, tools_requested=True, risk_level="A1", need_quality_gate=True, final_output_contract="execution_report")


def test_provider_native_routing_and_readiness() -> None:
    openai_cfg = ModelConfig(provider="openai", model="gpt-5-test", api_key="mockkey_test-not-real")
    anthropic_cfg = ModelConfig(provider="claude", model="claude-test", api_key="mockkey_ant-test-not-real")
    fable_cfg = ModelConfig(provider="fable", model="fable-5-test", api_key="mockkey_ant-test-not-real")
    gemini_cfg = ModelConfig(provider="gemini", model="gemini-test", api_key="AIza-test-not-real")
    deepseek_cfg = ModelConfig(provider="deepseek", model="deepseek-v4-pro", api_key="mockkey_test-not-real", base_url="https://api.deepseek.example")
    qwen_cfg = ModelConfig(provider="qwen", model="qwen-plus", api_key="mockkey_test-not-real", base_url="https://dashscope.example/compatible-mode/v1")
    assert_true(isinstance(select_model_client(openai_cfg), OpenAINativeAdapter), "openai must use native adapter")
    assert_true(isinstance(select_model_client(anthropic_cfg), AnthropicNativeAdapter), "claude/anthropic must use native adapter")
    assert_true(isinstance(select_model_client(fable_cfg), AnthropicNativeAdapter), "fable must use anthropic native adapter")
    assert_true(isinstance(select_model_client(gemini_cfg), GeminiNativeAdapter), "gemini must use native adapter")
    assert_true(isinstance(select_model_client(deepseek_cfg), OpenAICompatibleAdapter), "deepseek remains openai-compatible")
    assert_true(isinstance(select_model_client(qwen_cfg), OpenAICompatibleAdapter), "qwen remains openai-compatible")
    assert_true(provider_is_ready(openai_cfg), "openai native readiness must not require base_url")
    assert_true(provider_is_ready(anthropic_cfg), "anthropic native readiness must not require base_url")
    assert_true(provider_is_ready(gemini_cfg), "gemini native readiness must not require base_url")
    assert_true(provider_is_ready(deepseek_cfg), "openai-compatible readiness still requires base_url/api_key/model")


def test_provider_error_classification() -> None:
    assert_true(classify_provider_error(provider="x", status_code=401).kind is ProviderErrorKind.AUTH_ERROR, "401 must map to auth_error")
    assert_true(classify_provider_error(provider="x", status_code=404).kind is ProviderErrorKind.MODEL_NOT_FOUND, "404 must map to model_not_found")
    assert_true(classify_provider_error(provider="x", status_code=429).kind is ProviderErrorKind.RATE_LIMITED, "429 must map to rate_limited")
    assert_true(classify_provider_error(provider="x", detail="maximum context length exceeded").kind is ProviderErrorKind.CONTEXT_OVERFLOW, "context text must map to context_overflow")
    assert_true(classify_provider_error(provider="x", detail="request timed out").kind is ProviderErrorKind.TIMEOUT, "timeout text must map to timeout")


def test_active_policy_roles() -> None:
    adapter = ModelCapabilityAdapter()
    engine = ModelExecutionPolicyEngine()
    profiles = {
        "strong": adapter.resolve_profile(ModelConfig(provider="openai", model="gpt-5-test", api_key="mockkey_test")),
        "guarded": adapter.resolve_profile(ModelConfig(provider="deepseek", model="deepseek-v4-pro", api_key="mockkey_test", base_url="https://api.example")),
        "micro": adapter.resolve_profile(ModelConfig(provider="qwen", model="qwen-plus", api_key="mockkey_test", base_url="https://api.example")),
        "weak": adapter.resolve_profile(ModelConfig(provider="weak", model="weak-tiny", api_key="mockkey_test", base_url="https://api.example")),
    }
    strong = engine.activate(profiles["strong"], adapter.resolve_policy(profiles["strong"]), requested_max_steps=50)
    guarded = engine.activate(profiles["guarded"], adapter.resolve_policy(profiles["guarded"]), requested_max_steps=50)
    micro = engine.activate(profiles["micro"], adapter.resolve_policy(profiles["micro"]), requested_max_steps=50)
    weak = engine.activate(profiles["weak"], adapter.resolve_policy(profiles["weak"]), requested_max_steps=50)
    assert_true(strong.allowed_work_mode and strong.effective_max_steps <= 20 and strong.prompt_contract == "strict_json", "strong policy must allow capped long-chain")
    assert_true(guarded.allowed_work_mode and guarded.effective_max_steps <= 8 and guarded.prompt_contract == "short_json", "guarded policy must use short_json")
    assert_true(micro.allowed_work_mode and micro.effective_max_steps <= 3 and micro.prompt_contract == "choice_or_short_json", "micro policy must clamp to 1-3 steps")
    assert_true(not weak.allowed_work_mode and weak.failure_kind == "weak_model_not_allowed", "weak model must not be main brain")


def test_weak_model_blocked_before_planner_and_not_in_conversation() -> None:
    result = RuntimeEntry().run_text(
        "修复这个项目",
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=ModelConfig(provider="weak", model="weak-tiny", api_key="mockkey_test", base_url="https://api.example"),
        model_client=FailIfCalledClient(),
        activation_form=work_form("code"),
    )
    assert_true(result.status == "model_required", "weak model should produce model_required")
    assert_true(result.failure_kind == "weak_model_not_allowed", "weak failure_kind must be explicit")
    assert_true(result.active_model_policy is not None and not result.active_model_policy.allowed_work_mode, "active policy must be present and blocked")
    events = runtime_result_to_sse_events(result)
    conversation = [e for e in events if e["display_channel"] == "conversation"]
    workbench = [e for e in events if e["display_channel"] == "workbench"]
    conversation_text = json.dumps([e["payload"] for e in conversation], ensure_ascii=False)
    workbench_text = json.dumps([e["payload"] for e in workbench], ensure_ascii=False)
    assert_true("active_model_policy" not in conversation_text and "tool_name" not in conversation_text, "conversation must not expose model policy/tool details")
    assert_true("active_model_policy" in workbench_text and "weak_model_not_allowed" in workbench_text, "workbench must carry policy diagnostics")


def test_micro_planner_executes_only_three_steps() -> None:
    plan = {
        "steps": [
            {"tool_name": "write_workspace_file", "arguments": {"path": "hello.txt", "content": "abc"}, "reason": "create"},
            {"tool_name": "list_dir", "arguments": {"path": "."}, "reason": "verify list"},
            {"tool_name": "read_file", "arguments": {"path": "hello.txt"}, "reason": "verify content"},
            {"tool_name": "list_dir", "arguments": {"path": "."}, "reason": "should be truncated by schema/policy"},
            {"tool_name": "list_dir", "arguments": {"path": "."}, "reason": "should be truncated by schema/policy"},
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        result = RuntimeEntry().run_text(
            "创建 hello.txt 内容 abc",
            workspace=tmp,
            planner_mode=PlannerMode.MODEL_SUGGEST,
            model_config=ModelConfig(provider="qwen", model="qwen-plus", api_key="mockkey_test", base_url="https://api.example"),
            model_client=StaticPlanClient(plan),
            max_steps=10,
            activation_form=work_form("file"),
        )
        assert_true(result.active_model_policy is not None and result.active_model_policy.model_role == "micro_planner", "qwen must be micro_planner")
        assert_true(len(result.plan) <= 3 and len(result.results) <= 3, "micro planner must be capped to 3 steps")
        assert_true(Path(tmp, "hello.txt").read_text(encoding="utf-8") == "abc", "file task must still execute and verify")


def test_micro_planner_blocks_complex_code_tool_plan() -> None:
    plan = {"steps": [{"tool_name": "scan_project", "arguments": {"path": "."}, "reason": "complex repo scan"}]}
    result = RuntimeEntry().run_text(
        "修复这个项目",
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=ModelConfig(provider="qwen", model="qwen-plus", api_key="mockkey_test", base_url="https://api.example"),
        model_client=StaticPlanClient(plan),
        activation_form=work_form("code"),
    )
    assert_true(result.status == "model_required", "micro planner must not run complex Code-X plan as main brain")
    assert_true(result.failure_kind == "tool_plan_blocked_by_model_policy", "blocked tool family must be explicit")
    assert_true(not result.has_executed_tools, "blocked policy must not execute tools")


def test_context_overflow_compact_retry_and_timeout_classification() -> None:
    adapter = ModelCapabilityAdapter()
    cfg = ModelConfig(provider="openai", model="gpt-5-test", api_key="mockkey_test")
    profile = adapter.resolve_profile(cfg)
    passive = adapter.resolve_policy(profile)
    active = ModelExecutionPolicyEngine().activate(profile, passive, requested_max_steps=20)
    overflow_client = ContextOverflowThenOkClient()
    result = ModelPlanner().build_plan(
        "列目录",
        model_config=cfg,
        model_client=overflow_client,
        activation_form=work_form("file").public_dict(),
        active_model_policy=active,
        context_hint="x" * 9000,
    )
    assert_true(result.ok and result.repair_attempted and result.repair_stage == "context_overflow_compact_retry", "context_overflow must compact retry")
    assert_true(len(overflow_client.calls) == 2 and overflow_client.calls[-1].phase == "planner_execution_context_retry", "retry envelope must be used")
    timeout_result = ModelPlanner().build_plan(
        "列目录",
        model_config=cfg,
        model_client=TimeoutClient(),
        activation_form=work_form("file").public_dict(),
        active_model_policy=active,
    )
    assert_true(not timeout_result.ok and timeout_result.provider_status == "timeout" and timeout_result.failure_kind == "provider_timeout", "timeout must be classified")


def main() -> None:
    tests = [
        test_provider_native_routing_and_readiness,
        test_provider_error_classification,
        test_active_policy_roles,
        test_weak_model_blocked_before_planner_and_not_in_conversation,
        test_micro_planner_executes_only_three_steps,
        test_micro_planner_blocks_complex_code_tool_plan,
        test_context_overflow_compact_retry_and_timeout_classification,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("L6.72.58 ProviderNativeAdapterModelPolicy smoke PASS")


if __name__ == "__main__":
    main()
