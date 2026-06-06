from __future__ import annotations

import json

from tiangong_agent_runtime.frontend_contract import (
    CHAT_STREAM_ENDPOINT,
    CONTRACT_VERSION,
    FRONTEND_FORBIDDEN_ACTIONS,
    STATUS_BAR_FIELDS,
    build_frontend_backend_contract,
    build_provider_settings_contract,
    build_runtime_sse_event_schema,
    build_status_bar_fields_contract,
    provider_config_to_public_settings,
    runtime_result_to_sse_events,
    validate_frontend_contract,
)
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_shell.config_loader import ModelConfig, load_model_config
from tiangong_agent_shell.tool_bridge import ToolExecutionMode


def test_l6_51_contract_freezes_stream_endpoint_terminal_order_and_boundaries() -> None:
    contract = build_frontend_backend_contract()
    schema = contract["sse_schema"]

    assert contract["schema"] == CONTRACT_VERSION
    assert contract["chat_stream_endpoint"] == CHAT_STREAM_ENDPOINT == "/chat/stream-events"
    assert schema["transport"] == "sse"
    assert schema["terminal_order"] == ["assistant_final", "run_terminal"]
    assert "assistant_final" in schema["event_types"]
    assert "run_terminal" in schema["event_types"]
    assert contract["official_chain"] == "Planner -> ExecutionSpine -> Runtime -> QualityGate -> Audit/Rollback"
    assert "direct_provider_sdk_call" in contract["forbidden_frontend_actions"]
    assert "direct_long_term_memory_write" in contract["forbidden_frontend_actions"]
    assert "direct_self_iteration_merge" in contract["forbidden_frontend_actions"]


def test_l6_51_provider_settings_are_write_only_for_credentials_and_endpoint() -> None:
    provider_contract = build_provider_settings_contract()
    assert "api_key" in provider_contract["write_only_fields"]
    assert "base_url" in provider_contract["write_only_fields"]
    assert "api_key" not in provider_contract["read_fields"]
    assert "base_url" not in provider_contract["read_fields"]
    assert "api_key" in provider_contract["forbidden_response_fields"]
    assert "base_url" in provider_contract["forbidden_response_fields"]

    config = ModelConfig(
        provider="openai_compatible",
        base_url="https://deepseek.example.invalid/v1",
        api_key="sk-live-l6-51-contract-secret",
        model="deepseek-v4-pro",
        tool_execution_mode=ToolExecutionMode.DISABLED,
        planner_mode=PlannerMode.MODEL_SUGGEST,
    )
    public = provider_config_to_public_settings(config)
    raw = json.dumps(public, ensure_ascii=False)
    assert public["api_key_configured"] is True
    assert "base_url_digest" in public
    assert "deepseek.example" not in raw
    assert "sk-live-l6-51-contract-secret" not in raw
    assert "api_key" not in public
    assert "base_url" not in public


def test_l6_51_deepseek_env_aliases_enter_controlled_model_config(monkeypatch) -> None:
    monkeypatch.delenv("TIANGONG_API_KEY", raising=False)
    monkeypatch.delenv("TIANGONG_BASE_URL", raising=False)
    monkeypatch.delenv("TIANGONG_MODEL", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-l6-51-env-alias-secret")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://deepseek.example.invalid/v1")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

    config = load_model_config()
    assert config.api_key == "sk-l6-51-env-alias-secret"
    assert config.base_url == "https://deepseek.example.invalid/v1"
    assert config.model == "deepseek-v4-flash"
    raw = json.dumps(config.sanitized_dict(), ensure_ascii=False)
    assert "sk-l6-51-env-alias-secret" not in raw
    assert "deepseek.example" not in raw


def test_l6_51_status_bar_fields_are_stable_and_minimal() -> None:
    status_contract = build_status_bar_fields_contract()
    assert tuple(status_contract["required_fields"]) == STATUS_BAR_FIELDS
    assert status_contract["minimal_home_rule"]["fixed_chat_input_required"] is True
    assert status_contract["minimal_home_rule"]["home_should_stay_minimal"] is True
    assert status_contract["minimal_home_rule"]["no_monitor_wall_by_default"] is True
    assert set(STATUS_BAR_FIELDS) == {
        "runtime_status",
        "provider_model",
        "budget_pool",
        "budget_used_ratio",
        "gate_status",
        "audit_id",
        "memory_mode",
        "tools_allowed",
        "latency_ms",
    }


def test_l6_51_runtime_result_projects_to_ordered_sse_without_secret_leak(tmp_path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_text(
        "write reports/l6_51_frontend_contract_tmp.txt :: api_key=sk-should-not-leak endpoint=https://secret.example/v1",
        workspace=tmp_path,
        planner_mode=PlannerMode.RULE_ONLY,
        tool_mode=ToolExecutionMode.DRY_RUN,
        max_steps=1,
    )
    events = runtime_result_to_sse_events(result, run_id="run_l6_51_test", task_id="task_l6_51_contract")
    names = [event["event"] for event in events]
    assert names[-2:] == ["assistant_final", "run_terminal"]
    assert names.index("assistant_final") < names.index("run_terminal")
    assert all(event["seq"] == index for index, event in enumerate(events, start=1))
    raw = json.dumps(events, ensure_ascii=False)
    assert "sk-should-not-leak" not in raw
    assert "secret.example" not in raw
    assert "api_key=" not in raw
    assert "endpoint=https" not in raw


def test_l6_51_contract_validator_and_schema_are_self_consistent() -> None:
    check = validate_frontend_contract()
    assert check.ok is True
    assert check.issues == ()
    schema = build_runtime_sse_event_schema()
    for event_name, event_schema in schema["events"].items():
        assert event_name in schema["event_types"]
        assert set(schema["required_envelope_fields"]).issubset(event_schema.keys())
    assert "direct_provider_sdk_call" in FRONTEND_FORBIDDEN_ACTIONS
