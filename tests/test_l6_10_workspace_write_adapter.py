from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry


def test_write_creates_backup_when_overwriting(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("old", encoding="utf-8")
    result = RuntimeEntry().run_text("write a.txt :: new", workspace=tmp_path, tool_mode="runtime_governed")
    assert result.projection.status == "ok"
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "new"
    assert list(tmp_path.glob("a.txt.bak_*"))


def test_write_absolute_path_requires_confirmation(tmp_path: Path) -> None:
    target = tmp_path / "abs.txt"
    result = RuntimeEntry().run_text(f"write {target} :: x", workspace=tmp_path, tool_mode="runtime_governed")
    assert result.results[0].status.value == "confirmation_required"
    assert not target.exists()
