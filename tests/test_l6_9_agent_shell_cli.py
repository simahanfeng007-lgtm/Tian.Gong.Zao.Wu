from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )


def test_run_agent_help_returns_zero() -> None:
    proc = run_cmd("run_agent.py", "--help")
    assert proc.returncode == 0
    assert "天工造物 v2" in proc.stdout


def test_run_agent_mock_once_returns_mock_reply() -> None:
    proc = run_cmd("run_agent.py", "--mock", "--once", "你好")
    assert proc.returncode == 0
    assert "[MOCK] 已收到：你好" in proc.stdout


def test_agent_shell_module_mock_once_returns_mock_reply() -> None:
    proc = run_cmd("-m", "tiangong_agent_shell", "--mock", "--once", "你好")
    assert proc.returncode == 0
    assert "[MOCK] 已收到：你好" in proc.stdout


def test_status_does_not_crash_without_api_key() -> None:
    proc = run_cmd("run_agent.py", "--status")
    assert proc.returncode == 0
    assert "credential_state: <未配置>" in proc.stdout
    assert "<未配置>" in proc.stdout
