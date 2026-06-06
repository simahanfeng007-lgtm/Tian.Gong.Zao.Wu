from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry


def test_runtime_can_list_read_write_and_package(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    (tmp_path / "input.txt").write_text("hello", encoding="utf-8")

    listed = runtime.run_text("list .", workspace=tmp_path, tool_mode="runtime_governed")
    assert listed.projection.status == "ok"
    assert "input.txt" in listed.projection.summary

    read = runtime.run_text("read input.txt", workspace=tmp_path, tool_mode="runtime_governed")
    assert read.projection.status == "ok"
    assert "hello" in read.projection.summary

    written = runtime.run_text("write out.txt :: world", workspace=tmp_path, tool_mode="runtime_governed")
    assert written.projection.status == "ok"
    assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "world"

    packaged = runtime.run_text("zip . dist/test.zip", workspace=tmp_path, tool_mode="runtime_governed")
    assert packaged.projection.status == "ok"
    assert (tmp_path / "dist" / "test.zip").exists()
    assert (tmp_path / "dist" / "test.zip.sha256").exists()


def test_runtime_dry_run_does_not_write(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_text("write out.txt :: world", workspace=tmp_path, tool_mode="dry_run")
    assert result.projection.status == "partial_or_failed"
    assert not (tmp_path / "out.txt").exists()
