from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient
from linyuanzhe_frontend.contracts.sse_events import RuntimeSseEvent
from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def apply(client: SseRuntimeClient, event: str, seq: int, payload: dict) -> None:
    client._apply_event(RuntimeSseEvent(event=event, seq=seq, run_id="local_run_smoke", task_id="task_smoke", payload=payload))


def main() -> None:
    require((FE_RUNTIME_VERSION.startswith(("L6.72.", "L6.73.")) or FE_RUNTIME_VERSION.startswith("L6.73.")), "frontend version must be L6.72.52")
    client = SseRuntimeClient("http://127.0.0.1:8787")
    client._snapshot.chat_messages = []
    client._transcript.clear()

    apply(client, "run_started", 1, {"frontend_work_mode": "work", "provider_model": "deepseek-v4-pro"})
    apply(client, "run_accepted", 2, {"phase": "创建项目骨架"})
    apply(client, "planner_started", 3, {"planner_mode": "model_suggest"})
    apply(client, "planner_plan", 4, {"steps": [
        {"name": "创建 Flask 项目", "goal": "生成目录结构"},
        {"name": "写入 README", "goal": "说明本地部署方式"},
    ]})
    apply(client, "tool_started", 5, {"tool_name": "write_file", "message": "写入 app.py"})
    apply(client, "tool_progress", 6, {"tool_name": "write_file", "message": "app.py 已写入 70%"})
    apply(client, "tool_result", 7, {"tool_name": "write_file", "status": "ok", "output_summary": "app.py 已写入"})
    apply(client, "assistant_final", 8, {"content": "• readfile: ok | from flask import Flask\n已就位。项目骨架已生成。", "status": "ok"})
    apply(client, "run_terminal", 9, {"status": "ok"})

    transcript = "\n".join(message.text for message in client._snapshot.chat_messages)
    # L6.72.54+ separates conversation from workflow telemetry: progress/tool
    # events must not pollute the chat transcript. The final concise summary
    # remains visible to the user.
    for marker in ("工作任务已启动", "长链任务已启动", "执行计划已生成", "正在执行步骤", "步骤进展", "步骤已返回", "任务已收口"):
        require(marker not in transcript, f"workflow marker leaked into chat transcript: {marker}")
    require("from flask import" not in transcript, "raw readfile output must be hidden from main transcript")
    require("已就位" in transcript, "final user-facing summary should be preserved")

    snap = client.try_handle_status_probe("咋样了？")
    require(snap is not None, "status probe should be handled locally")
    status_transcript = "\n".join(message.text for message in snap.chat_messages)
    require(("当前任务状态" in status_transcript) or ("当前没有运行中的工作任务" in status_transcript), "status probe should append task status or idle summary")
    require(("Run：" in status_transcript) or ("当前没有运行中的工作任务" in status_transcript), "status probe should include run id or idle summary")

    print("PASS L6.72.52 work_chat_progress_smoke")


if __name__ == "__main__":
    main()
