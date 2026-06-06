from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry


def test_read_file_blocks_sensitive_name(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("TIANGONG_API_KEY=secret", encoding="utf-8")
    result = RuntimeEntry().run_text("read .env", workspace=tmp_path, tool_mode="runtime_governed")
    assert result.results[0].status.value == "blocked"


def test_read_file_blocks_outside_workspace(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    result = RuntimeEntry().run_text(f"read {outside}", workspace=tmp_path, tool_mode="runtime_governed")
    assert result.results[0].status.value in {"blocked", "confirmation_required"}
