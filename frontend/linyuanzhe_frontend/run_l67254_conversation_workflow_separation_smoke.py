"""L6.72.54 会话区/工作流分离 smoke。"""

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
from linyuanzhe_frontend.contracts.sse_events import RuntimeSseEvent  # noqa: E402


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    client = SseRuntimeClient(base_url="http://127.0.0.1:1")
    client._transcript.append_message(ChatMessage("user", "你", "12:00", "请进入工作模式并执行长链任务"))
    client._sync_transcript_projection()

    client._apply_event(RuntimeSseEvent(event="run_started", seq=1, run_id="run_l67254", task_id="task_l67254", display_channel="status", visibility="progress", event_kind="task_progress", payload={"runtime_status": "active"}))
    client._apply_event(RuntimeSseEvent(event="planner_plan", seq=2, run_id="run_l67254", task_id="task_l67254", display_channel="workbench", visibility="task_telemetry", event_kind="task_progress", payload={"steps": [{"tool_name": "list_dir", "arguments": {"path": "."}}, {"tool_name": "write_workspace_file", "arguments": {"path": "a.txt", "content": "x"}}]}))
    for i in range(20):
        client._apply_event(RuntimeSseEvent(event="tool_started", seq=3 + i * 2, run_id="run_l67254", task_id="task_l67254", display_channel="workbench", visibility="task_telemetry", event_kind="tool_step", payload={"step_id": f"step_{i}", "tool_name": f"tool_{i}", "message": f"内部步骤 {i}"}))
        client._apply_event(RuntimeSseEvent(event="tool_result", seq=4 + i * 2, run_id="run_l67254", task_id="task_l67254", display_channel="workbench", visibility="task_telemetry", event_kind="tool_step", payload={"step_id": f"step_{i}", "tool_name": f"tool_{i}", "status": "ok", "output_summary": f"结果 {i}"}))
    client._apply_event(RuntimeSseEvent(event="execution_report", seq=80, run_id="run_l67254", task_id="task_l67254", display_channel="workbench", visibility="artifact", event_kind="final", payload={"status": "ok", "summary": "- tool_0: ok\\n- tool_1: ok", "artifacts": ["a.txt"]}))
    client._apply_event(RuntimeSseEvent(event="assistant_final", seq=81, run_id="run_l67254", task_id="task_l67254", display_channel="conversation", visibility="user_dialogue", event_kind="final", payload={"status": "ok", "content": "任务已完成。完整执行详情已放入任务工作台。"}))
    client._apply_event(RuntimeSseEvent(event="run_terminal", seq=82, run_id="run_l67254", task_id="task_l67254", display_channel="status", visibility="progress", event_kind="final", payload={"status": "ok", "terminal": True}))

    snap = client.get_snapshot()
    texts = [item.text for item in snap.chat_messages]
    assert_true(len(texts) == 2, f"conversation must contain only user + final assistant, got {len(texts)}: {texts}")
    joined = "\n".join(texts)
    assert_true("tool_" not in joined and "内部步骤" not in joined and "write_workspace_file" not in joined, "workflow/tool details must not enter conversation transcript")
    assert_true("任务已完成" in joined, "final brief summary must remain visible")
    assert_true(len(snap.execution_steps) >= 20, "workflow steps must remain visible in workbench projection")
    assert_true(snap.run_workbench_state in {"completed", "tool_running", "planning", "streaming"}, "workbench state must be active/completed")
    print("PASS L6.72.54 conversation/workflow separation smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
