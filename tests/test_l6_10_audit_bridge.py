from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry


def test_audit_event_is_recorded(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    runtime.run_text("list .", workspace=tmp_path, tool_mode="runtime_governed")
    events = runtime.audit.recent_summary()
    assert len(events) == 1
    assert events[0]["tool_name"] == "list_dir"
    assert events[0]["risk_level"] == "A1"
