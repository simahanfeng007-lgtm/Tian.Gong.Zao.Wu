from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry


def test_a4_confirmation_ticket_can_be_confirmed_without_bypassing_adapter(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    absolute_target = tmp_path / "confirmed.txt"
    first = runtime.run_text(
        f"write {absolute_target} :: hello-confirm",
        workspace=tmp_path,
        tool_mode="runtime_governed",
    )
    assert first.results[0].status.value == "confirmation_required"
    pending = runtime.pending_confirmations()
    assert len(pending) == 1
    ticket_id = pending[0]["ticket_id"]
    assert pending[0]["risk_level"] == "A4"
    assert not absolute_target.exists()

    confirmed = runtime.confirm_ticket(ticket_id, workspace=tmp_path, tool_mode="runtime_governed")
    assert confirmed.results[0].status.value == "ok"
    assert absolute_target.read_text(encoding="utf-8") == "hello-confirm"
    assert runtime.pending_confirmations() == []
    events = runtime.audit.recent_summary()
    assert events[-2]["permit_status"] == "confirmation_required"
    assert events[-1]["permit_status"] == "allowed"


def test_denied_ticket_cannot_be_confirmed(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    absolute_target = tmp_path / "denied.txt"
    first = runtime.run_text(
        f"write {absolute_target} :: should-not-write",
        workspace=tmp_path,
        tool_mode="runtime_governed",
    )
    ticket_id = first.pending_confirmations[0]["ticket_id"]  # type: ignore[index]
    denied = runtime.deny_ticket(ticket_id)
    assert denied["ok"] is True
    confirmed = runtime.confirm_ticket(ticket_id, workspace=tmp_path, tool_mode="runtime_governed")
    assert confirmed.results[0].status.value == "failed"
    assert confirmed.results[0].error_code == "ticket_not_pending"
    assert not absolute_target.exists()
