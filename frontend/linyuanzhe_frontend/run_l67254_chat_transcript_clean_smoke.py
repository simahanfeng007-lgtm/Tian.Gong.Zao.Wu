"""L6.72.54 长链 100 事件后聊天 transcript 仍清爽 smoke。"""

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


def main() -> int:
    client = SseRuntimeClient(base_url="http://127.0.0.1:1")
    client._transcript.append_message(ChatMessage("user", "你", "12:00", "执行 100 步长链任务"))
    client._sync_transcript_projection()
    for i in range(100):
        client._apply_event(RuntimeSseEvent(event="tool_started", seq=i + 1, run_id="run_100", task_id="task_100", display_channel="workbench", visibility="task_telemetry", event_kind="tool_step", payload={"step_id": f"s{i}", "tool_name": f"tool_{i}", "message": f"Step {i}"}))
    client._apply_event(RuntimeSseEvent(event="assistant_final", seq=101, run_id="run_100", task_id="task_100", display_channel="conversation", visibility="user_dialogue", event_kind="final", payload={"status": "ok", "content": "任务已完成。完整执行详情已放入任务工作台。"}))
    snap = client.get_snapshot()
    assert len(snap.chat_messages) == 2, [item.text for item in snap.chat_messages]
    transcript = "\n".join(item.text for item in snap.chat_messages)
    assert "Step" not in transcript and "tool_" not in transcript and "工具/步骤" not in transcript, transcript
    assert len(snap.execution_steps) == 100, len(snap.execution_steps)
    print("PASS L6.72.54 chat transcript clean smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
