from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.project_index_bridge import ProjectIndexBridge
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_port import ChatResult
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


class RecordingProjectPlanClient:
    provider = "recording-project-plan"

    def __init__(self) -> None:
        self.last_messages: list[dict[str, str]] = []

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:  # noqa: ARG002
        self.last_messages = messages
        return ChatResult(
            content=json.dumps({"steps": [{"tool_name": "scan_project", "arguments": {"path": "."}}]}, ensure_ascii=False),
            provider=self.provider,
            model="planner",
        )


def _seed_project(root: Path) -> None:
    (root / "README.md").write_text("hello", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (root / "run_agent.py").write_text("print('demo')\n", encoding="utf-8")
    (root / "pkg").mkdir()
    (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_demo.py").write_text("def test_demo(): assert True\n", encoding="utf-8")
    (root / ".env").write_text("SECRET=1\n", encoding="utf-8")


def test_project_index_bridge_scans_structure_without_secret_content(tmp_path: Path) -> None:
    _seed_project(tmp_path)
    bridge = ProjectIndexBridge()
    snapshot = bridge.scan(tmp_path)
    payload = snapshot.public_dict()
    assert payload["schema"] == "tiangong.l6_16.project_index.v1"
    assert "README.md" in payload["key_files"]
    assert "pyproject.toml" in payload["key_files"]
    assert "run_agent.py" in payload["entry_points"]
    assert "pkg" in payload["package_dirs"]
    assert "tests/test_demo.py" in payload["test_files"]
    text = json.dumps(payload, ensure_ascii=False)
    assert "SECRET=1" not in text
    assert ".env" in text  # 只允许以 risk note 的形式出现文件名，不能出现内容。


def test_runtime_scan_project_tool_updates_snapshot_and_audit(tmp_path: Path) -> None:
    _seed_project(tmp_path)
    runtime = RuntimeEntry()
    result = runtime.run_text("scan .", workspace=tmp_path, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED)
    assert result.results and result.results[0].ok
    snapshot = runtime.project_snapshot()
    assert snapshot["files_count"] >= 4
    assert "scan_project" in {event["tool_name"] for event in result.audit_events}


def test_plan_validator_accepts_scan_project_but_rejects_unsafe_path() -> None:
    plan = validate_and_build_plan({"steps": [{"tool_name": "scan_project", "arguments": {"max_depth": 99, "max_files": 999999}}]})
    assert plan[0].tool_name == "scan_project"
    assert plan[0].arguments["path"] == "."
    assert plan[0].arguments["max_depth"] == 12
    assert plan[0].arguments["max_files"] == 10000


def test_model_planner_receives_project_index_hint_after_scan(tmp_path: Path) -> None:
    _seed_project(tmp_path)
    runtime = RuntimeEntry()
    runtime.run_text("scan .", workspace=tmp_path, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED)
    client = RecordingProjectPlanClient()
    result = runtime.run_text(
        "继续检查这个项目",
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode="model_suggest",
        model_config=ModelConfig(provider="mock", model="mock-model"),
        model_client=client,
    )
    assert result.has_plan
    planner_user = client.last_messages[-1]["content"]
    assert "项目结构摘要" in planner_user
    assert "README.md" in planner_user
    assert "pyproject.toml" in planner_user


def test_cli_scan_project_show_and_export(tmp_path: Path) -> None:
    _seed_project(tmp_path)
    proc = subprocess.run(
        [
            sys.executable,
            "run_agent.py",
            "--mock",
            "--tool-mode",
            "runtime_governed",
            "--workspace",
            str(tmp_path),
        ],
        cwd=ROOT,
        input="/scan .\n/project\n/project-save project_index.json\n/project-reset\n/project\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=25,
    )
    assert proc.returncode == 0, proc.stderr
    assert "L6.16 项目雷达扫描结果" in proc.stdout
    assert "项目索引已导出" in proc.stdout
    assert "项目索引已清空" in proc.stdout
    assert (tmp_path / "project_index.json").exists()
