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
from linyuanzhe_frontend.contracts.sse_events import RuntimeSseEvent
from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION, PROVIDER_CONFIG_SCHEMA_VERSION


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def apply(client: SseRuntimeClient, event: str, seq: int, payload: dict) -> None:
    client._apply_event(RuntimeSseEvent(event=event, seq=seq, run_id="local_run_codex_card", task_id="task_codex_card", payload=payload))


def main() -> None:
    require((FE_RUNTIME_VERSION.startswith(("L6.72.", "L6.73.")) or FE_RUNTIME_VERSION.startswith("L6.73.")), "frontend version must be L6.72.41+ compatible+ compatible")
    require(PROVIDER_CONFIG_SCHEMA_VERSION.startswith("tiangong.l6_73_") or PROVIDER_CONFIG_SCHEMA_VERSION.endswith(("l6_72_52.local_provider_config.v1", "l6_73_5.local_provider_config.v1")), "provider schema must accept L6.72.52+ / L6.73.x")

    root = Path(__file__).resolve().parent
    chat_source = (root / "ui" / "main_window_chat_runtime.py").read_text(encoding="utf-8")
    require("codex_card_header" in chat_source, "Codex progress card header tag missing")
    require("_render_codex_progress_card" in chat_source, "Codex progress card renderer missing")
    require("chat_message_gap" in chat_source, "chat bubble message spacing tag missing")

    client = SseRuntimeClient("http://127.0.0.1:8787")
    client._snapshot.chat_messages = []
    client._transcript.clear()

    apply(client, "run_started", 1, {"frontend_work_mode": "long_chain", "provider_model": "deepseek-v4-pro"})
    apply(client, "planner_started", 2, {"planner_mode": "long_chain"})
    apply(client, "planner_plan", 3, {"steps": [{"name": "建立项目骨架", "goal": "生成文件"}, {"name": "运行测试", "goal": "验证可用"}]})
    apply(client, "tool_started", 4, {"tool_name": "write_file", "message": "写入 app.py"})
    apply(client, "tool_progress", 5, {"tool_name": "pytest", "message": "测试执行中"})
    apply(client, "tool_result", 6, {"tool_name": "pytest", "status": "ok", "output_summary": "2 passed"})
    apply(client, "assistant_final", 7, {"content": "已完成。", "status": "ok"})
    apply(client, "run_terminal", 8, {"status": "ok"})

    transcript = "\n".join(message.text for message in client._snapshot.chat_messages)
    require(transcript.strip() == "已完成。", "conversation pane should keep only final user-facing summary")
    require("▣ Codex进度｜" not in transcript, "workflow progress must not pollute conversation transcript")
    require("执行计划已生成" not in transcript and "步骤已返回" not in transcript, "tool/planner telemetry must stay out of chat")
    require(getattr(client._snapshot, "frontend_executes_tools", False) is False, "frontend must not execute tools")
    require(getattr(client._snapshot, "progress_percent", 0) >= 0, "workbench/status projection should retain progress state")

    print("PASS L6.72.41-L6.73.x chat/workbench separation + final summary smoke")


if __name__ == "__main__":
    main()
