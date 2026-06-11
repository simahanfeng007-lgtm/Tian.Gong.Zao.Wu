"""L6.72.59 前端 RC 人类使用化专项 smoke。

覆盖：
- Runtime 新终态 completed_pass / completed_with_warnings / deterministic_fallback 不被误判失败。
- recoverable / provider_not_ready / model_required 进入可恢复工作台状态。
- 工作流事件不进入会话 transcript。
- 启动提示明确写入任务工作台，不再暗示刷会话区。
"""

from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))


from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient  # noqa: E402
from linyuanzhe_frontend.contracts.runtime_snapshot import ChatMessage  # noqa: E402
from linyuanzhe_frontend.contracts.run_workbench import normalize_run_state  # noqa: E402
from linyuanzhe_frontend.contracts.sse_events import RuntimeSseEvent  # noqa: E402


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _event(name: str, seq: int, *, channel: str, visibility: str, kind: str, payload: dict) -> RuntimeSseEvent:
    return RuntimeSseEvent(
        event=name,
        seq=seq,
        run_id="run_l67259_frontend",
        task_id="task_l67259_frontend",
        display_channel=channel,
        visibility=visibility,
        event_kind=kind,
        payload=payload,
    )


def test_runtime_status_normalization() -> None:
    assert_true(normalize_run_state("completed_pass") == "completed", "completed_pass must normalize to completed")
    assert_true(normalize_run_state("completed_with_warnings") == "completed", "completed_with_warnings must normalize to completed")
    assert_true(normalize_run_state("deterministic_fallback") == "completed", "deterministic_fallback must normalize to completed")
    assert_true(normalize_run_state("failed_recoverable") == "recoverable", "failed_recoverable must normalize to recoverable")
    assert_true(normalize_run_state("partial_with_resume") == "recoverable", "partial_with_resume must normalize to recoverable")
    assert_true(normalize_run_state("provider_not_ready") == "recoverable", "provider_not_ready must normalize to recoverable")
    assert_true(normalize_run_state("model_required") == "recoverable", "model_required must normalize to recoverable")


def test_conversation_clean_and_rc_statuses() -> None:
    client = SseRuntimeClient(base_url="http://127.0.0.1:1")
    client._transcript.append_message(ChatMessage("user", "你", "12:00", "进入工作模式，执行一个长链任务"))
    client._sync_transcript_projection()

    client._apply_event(_event(
        "run_started",
        1,
        channel="status",
        visibility="progress",
        kind="task_progress",
        payload={"runtime_status": "active", "frontend_work_mode": "work"},
    ))
    snap = client.get_snapshot()
    assert_true("任务工作台" in snap.run_diagnostic_summary, "run_started notice must point users to workbench")
    assert_true("后续步骤会持续写入会话区" not in snap.run_diagnostic_summary, "run_started notice must not promise workflow in conversation pane")

    client._apply_event(_event(
        "planner_plan",
        2,
        channel="workbench",
        visibility="task_telemetry",
        kind="task_progress",
        payload={"steps": [{"tool_name": "write_workspace_file", "arguments": {"path": "hello.txt"}}]},
    ))
    for i in range(100):
        client._apply_event(_event(
            "tool_started",
            3 + i * 2,
            channel="workbench",
            visibility="task_telemetry",
            kind="tool_step",
            payload={"step_id": f"step_{i}", "tool_name": f"tool_{i}", "message": f"内部工作流步骤 {i}"},
        ))
        client._apply_event(_event(
            "tool_result",
            4 + i * 2,
            channel="workbench",
            visibility="task_telemetry",
            kind="tool_step",
            payload={"step_id": f"step_{i}", "tool_name": f"tool_{i}", "status": "completed_pass", "output_summary": f"工具结果 {i}"},
        ))

    client._apply_event(_event(
        "execution_report",
        210,
        channel="workbench",
        visibility="artifact",
        kind="final",
        payload={"status": "completed_pass", "summary": "完整执行报告：write_workspace_file / tool_0 / tool_1", "artifacts": ["hello.txt"]},
    ))
    client._apply_event(_event(
        "assistant_final",
        211,
        channel="conversation",
        visibility="user_dialogue",
        kind="final",
        payload={"status": "completed_pass", "content": "任务已完成。完整执行详情已放入任务工作台。"},
    ))
    client._apply_event(_event(
        "run_terminal",
        212,
        channel="status",
        visibility="progress",
        kind="final",
        payload={"status": "completed_pass", "terminal": True},
    ))

    snap = client.get_snapshot()
    texts = [item.text for item in snap.chat_messages]
    joined = "\n".join(texts)
    assert_true(len(texts) == 2, f"conversation must contain only user + assistant final, got {len(texts)}: {texts}")
    assert_true("任务已完成" in joined, "brief final summary must remain in conversation")
    assert_true("tool_" not in joined and "内部工作流步骤" not in joined and "write_workspace_file" not in joined, "workflow details must not pollute conversation")
    assert_true(snap.current_task_status == "COMPLETED", f"completed_pass terminal must mark task completed, got {snap.current_task_status}")
    assert_true(snap.run_workbench_state == "completed", f"completed_pass terminal must mark workbench completed, got {snap.run_workbench_state}")
    assert_true(len(snap.execution_steps) >= 100, "workflow events must remain available in workbench projection")


def test_recoverable_statuses_remain_recoverable() -> None:
    for status in ["failed_recoverable", "partial_with_resume", "provider_not_ready", "model_required"]:
        client = SseRuntimeClient(base_url="http://127.0.0.1:1")
        client._apply_event(_event("run_started", 1, channel="status", visibility="progress", kind="task_progress", payload={"runtime_status": "active"}))
        client._apply_event(_event("assistant_final", 2, channel="conversation", visibility="user_dialogue", kind="final", payload={"status": status, "content": "任务可恢复，详情已放入任务工作台。"}))
        client._apply_event(_event("run_terminal", 3, channel="status", visibility="progress", kind="final", payload={"status": status, "terminal": True}))
        snap = client.get_snapshot()
        assert_true(snap.run_workbench_state in {"recoverable", "failed"}, f"{status} must not normalize to completed/idle; got {snap.run_workbench_state}")
        assert_true(snap.current_task_status != "COMPLETED", f"{status} must not mark task completed")


def main() -> int:
    test_runtime_status_normalization()
    test_conversation_clean_and_rc_statuses()
    test_recoverable_statuses_remain_recoverable()
    print("L6.72.59 frontend RC UX optimization smoke PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
