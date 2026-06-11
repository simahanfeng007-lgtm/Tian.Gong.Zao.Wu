from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



from pathlib import Path

from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient
from linyuanzhe_frontend.contracts.run_workbench import (
    RUN_WORKBENCH_CONTRACT_VERSION,
    RunWorkbenchProjection,
    normalize_run_state,
)
from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot
from linyuanzhe_frontend.contracts.sse_events import RuntimeSseEvent, SSE_EVENT_TYPES
from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def event(name: str, seq: int, **payload: object) -> RuntimeSseEvent:
    return RuntimeSseEvent.from_mapping(
        {
            "event": name,
            "seq": seq,
            "run_id": "run_l67227_smoke",
            "task_id": "task_l67227_smoke",
            "timestamp": "2026-06-09T00:00:00",
            "payload": payload,
        }
    )


def main() -> None:
    require((FE_RUNTIME_VERSION.startswith(("L6.72.", "L6.73.")) or FE_RUNTIME_VERSION.startswith("L6.73.")), "version not bumped to supported L6.72.27+ lineage")
    for name in {"run_accepted", "heartbeat", "approval_required", "tool_progress"}:
        require(name in SSE_EVENT_TYPES, f"missing SSE event type: {name}")
    require(RUN_WORKBENCH_CONTRACT_VERSION.endswith("desktop_run_workbench.v1"), "bad run workbench contract")
    require(normalize_run_state("running") == "tool_running", "running alias broken")

    projection = RunWorkbenchProjection.from_mapping({"state": "running", "run_id": "r", "task_id": "t"})
    require(projection.state == "tool_running", "projection state normalization broken")
    snapshot = RuntimeSnapshot(run_workbench_state="tool_running", active_run_id="r", active_task_id="t")
    require(snapshot.run_status_label == "工具运行中", "snapshot run label not synced")

    client = SseRuntimeClient("http://127.0.0.1:8787", timeout=60)
    sequence = [
        event("run_started", 1, frontend_work_mode="long_chain", long_chain_requested=True),
        event("run_accepted", 2, frontend_work_mode="long_chain", planner_mode="model_suggest", long_chain_requested=True),
        event("planner_started", 3, frontend_work_mode="long_chain", long_chain_requested=True),
        event("heartbeat", 4, heartbeat=True, elapsed_ms=1200, long_chain_requested=True),
        event("tool_started", 5, tool_name="RuntimeBackendSubprocess", status="running", long_chain_requested=True),
        event("tool_progress", 6, tool_name="RuntimeBackendSubprocess", status="running", long_chain_requested=True),
        event("tool_result", 7, tool_name="RuntimeBackendSubprocess", status="completed", long_chain_requested=True),
        event("assistant_delta", 8, delta="ok", long_chain_requested=True),
        event("assistant_final", 9, text="任务完成", long_chain_requested=True),
        event("run_terminal", 10, status="completed", long_chain_requested=True),
    ]
    for item in sequence:
        client._apply_event(item)  # smoke: private transition reducer only, no network/tool execution
    s = client.get_snapshot()
    require(s.run_workbench_state == "completed", f"final state wrong: {s.run_workbench_state}")
    require(s.run_status_label == "已完成", f"final label wrong: {s.run_status_label}")
    require(s.run_heartbeat_count >= 1, "heartbeat not counted")
    require(s.frontend_executes_tools is False, "frontend must not execute tools")
    require(s.current_tool_name == "RuntimeBackendSubprocess", "tool progress not projected")

    action_source = Path(__file__).resolve().parent / "ui" / "main_window_actions.py"
    action_text = action_source.read_text(encoding="utf-8")
    for token in {"_track_ime_input_event", "_is_ime_composing_event", "_copy_run_diagnostic", "get_run_status"}:
        require(token in action_text, f"missing UI workbench token: {token}")
    bridge_source = Path(__file__).resolve().parents[2] / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"
    bridge_text = bridge_source.read_text(encoding="utf-8")
    for token in {"/runs/status", "subprocess.Popen", "request_stop_active_runs", "run_accepted"}:
        require(token in bridge_text, f"missing bridge workbench token: {token}")
    print("L6.72.27-L6.72.33 desktop_run_workbench_smoke PASS")


if __name__ == "__main__":
    main()
