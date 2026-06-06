from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.public_projection_bridge import (
    L6_48_DESKTOP_PUBLIC_PROJECTION_SCHEMA,
    RuntimeProjection,
    build_desktop_dashboard_projection,
)

ROOT = Path(__file__).resolve().parents[1]
SECRET = "sk-l6-48-secret-credential-123456"
ENDPOINT = "https://api.secret-provider.example/v1"
RAW_PATH = "/tmp/tiangong/secret/config.json"


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )


def test_l6_48_desktop_dashboard_projection_is_readonly_and_sanitized() -> None:
    runtime_projection = RuntimeProjection(
        status="ok",
        summary=f"执行完成 api_key={SECRET} endpoint={ENDPOINT} path={RAW_PATH}",
        artifacts=[RAW_PATH],
        audit_count=2,
        chain={"total_steps": 7, "executed_steps": 6, "failure_count": 1, "stopped_reason": "quality_gate_review"},
        pending_confirmations=[{"ticket_id": "ticket:a4", "api_key": SECRET}],
    )

    dashboard = build_desktop_dashboard_projection(
        runtime_projection,
        task_title=f"封装核验 {ENDPOINT}",
        quality_gate={"decision": "review", "api_key": SECRET, "endpoint": ENDPOINT},
        audit_events=[{"audit_ref": "audit:1", "tool_name": "model_chat", "status": "ok", "secret": SECRET}],
        context_snapshot={"session_records": 3, "path": RAW_PATH},
        budget_snapshot={"current_consumption": 12, "balance": "unknown", "base_url": ENDPOINT},
        conversation_guide=f"继续核验，不展示 {SECRET} 或 {ENDPOINT}",
    )
    public = dashboard.public_dict()
    raw = json.dumps(public, ensure_ascii=False, sort_keys=True)

    assert public["schema"] == L6_48_DESKTOP_PUBLIC_PROJECTION_SCHEMA
    assert public["frontend_readonly"] is True
    assert public["projection_only"] is True
    assert public["no_direct_tool_call"] is True
    assert public["no_provider_sdk"] is True
    assert public["no_memory_write"] is True
    assert public["no_self_iteration_merge"] is True
    assert public["no_plain_endpoint"] is True
    assert public["no_plain_token"] is True
    assert set(["task_snapshot", "quality_gate", "audit_summary", "conversation_guide", "status_bar"]).issubset(public)
    assert SECRET not in raw
    assert ENDPOINT not in raw
    assert RAW_PATH not in raw
    assert public["sensitive_digest_refs"]


def test_l6_48_cli_status_and_config_do_not_show_plain_endpoint_or_key() -> None:
    status = run_cmd("run_agent.py", "--status", "--base-url", ENDPOINT, "--api-key", SECRET)
    assert status.returncode == 0, status.stderr
    assert SECRET not in status.stdout
    assert ENDPOINT not in status.stdout
    assert "endpoint_state: <已配置:digest:" in status.stdout
    assert "credential_state:" in status.stdout

    config = run_cmd("run_agent.py", "--show-config", "--base-url", ENDPOINT, "--api-key", SECRET)
    assert config.returncode == 0, config.stderr
    assert SECRET not in config.stdout
    assert ENDPOINT not in config.stdout
    assert '"base_url": "<已配置:digest:' in config.stdout
    assert '"api_key":' in config.stdout


def test_l6_48_startup_entry_keeps_shell_delegation_not_second_runtime() -> None:
    source = (ROOT / "run_agent.py").read_text(encoding="utf-8")
    assert "from tiangong_agent_shell.cli_main import main" in source
    assert "RuntimeEntry(" not in source
    assert "OpenAICompatibleModelClient(" not in source
