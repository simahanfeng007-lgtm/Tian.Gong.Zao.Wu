from __future__ import annotations

import json
from pathlib import Path

from tiangong_agent_runtime.audit_bridge import AuditBridge
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.runtime_report import export_runtime_report


def test_audit_export_and_replay_summary(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    runtime.run_text("write a.txt :: hello && read a.txt", workspace=tmp_path, tool_mode="runtime_governed")
    audit_path = tmp_path / "audit" / "runtime.jsonl"
    exported = runtime.export_audit_jsonl(audit_path)
    assert exported.exists()
    loaded = AuditBridge.load_jsonl(exported)
    assert len(loaded) == 2
    summary = runtime.replay_audit_jsonl(exported)
    assert summary.total_events == 2
    assert summary.by_tool["write_workspace_file"] == 1
    assert summary.by_tool["read_file"] == 1
    assert summary.by_status["ok"] == 2


def test_runtime_report_export_json_and_markdown(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_text("write report.txt :: ok", workspace=tmp_path, tool_mode="runtime_governed")
    json_path = export_runtime_report(result, tmp_path / "reports" / "run.json")
    md_path = export_runtime_report(result, tmp_path / "reports" / "run.md")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["projection"]["status"] == "ok"
    assert data["results"][0]["tool_name"] == "write_workspace_file"
    assert "天工造物 L6.32 运行报告" in md_path.read_text(encoding="utf-8")
