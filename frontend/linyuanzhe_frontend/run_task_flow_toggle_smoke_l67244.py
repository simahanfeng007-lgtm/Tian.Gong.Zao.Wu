from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



from pathlib import Path
import importlib.util

from linyuanzhe_frontend.contracts.work_modes import resolve_submit_work_mode, sanitize_work_mode_payload
from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient
from linyuanzhe_frontend.contracts.sse_events import RuntimeSseEvent


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def event(name: str, *, seq: int, run_id: str = "", task_id: str = "", payload: dict | None = None) -> RuntimeSseEvent:
    return RuntimeSseEvent.from_mapping({"event": name, "seq": seq, "run_id": run_id, "task_id": task_id, "payload": payload or {}})


def load_bridge_module(root: Path):
    bridge_path = root / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"
    spec = importlib.util.spec_from_file_location("linyuanzhe_bridge_l67251_smoke", bridge_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def main() -> int:
    root = Path(__file__).resolve().parents[2]

    chat = resolve_submit_work_mode("聊天", "你会做什么")
    assert_true(chat["mode"] == "chat" and not chat["planner_allowed"] and not chat["tools_requested"], "chat stays chat")
    work = resolve_submit_work_mode("工作", "修复这个 bug 并运行测试")
    assert_true(work["mode"] == "work" and work["planner_allowed"] and work["tools_requested"], "work triggers LLM activation task flow")
    code = resolve_submit_work_mode("代码", "运行 pytest")
    assert_true(code["mode"] == "work" and code["tools_requested"], "legacy code aliases to work")
    file_mode = resolve_submit_work_mode("文件", "读取桌面的 验收.docx")
    assert_true(file_mode["mode"] == "work" and file_mode["tools_requested"], "legacy file aliases to work")
    chain = resolve_submit_work_mode("长链", "修复这个 bug 并打包")
    assert_true(chain["mode"] == "work" and chain["planner_allowed"] and chain["tools_requested"], "legacy long_chain aliases to work")
    sanitized = sanitize_work_mode_payload({"mode": "chat", "planner_allowed": True, "tools_requested": True, "long_chain_requested": True})
    assert_true(sanitized["mode"] == "chat" and not sanitized["tools_requested"], "sanitize clamps forged chat task flags")

    client = SseRuntimeClient("http://127.0.0.1:8787")
    for item in [
        event("assistant_delta", seq=1, payload={"content": "你好，我可以正常聊天。"}),
        event("assistant_final", seq=2, payload={"status": "ok"}),
        event("run_terminal", seq=3, payload={"status": "ok"}),
    ]:
        client._apply_event(item)  # noqa: SLF001
    snap = client.get_snapshot()
    all_chat = "\n".join(getattr(m, "text", "") for m in snap.chat_messages)
    assert_true("Codex进度" not in all_chat, "ordinary chat has no task progress cards")
    assert_true(not snap.active_run_id and snap.run_workbench_state in {"idle", ""}, "ordinary chat does not occupy run workbench")

    client2 = SseRuntimeClient("http://127.0.0.1:8787")
    for item in [
        event("run_started", seq=1, run_id="run_work", task_id="task_1", payload={"frontend_work_mode": "work", "activation_requested": True}),
        event("planner_started", seq=2, run_id="run_work", task_id="task_1", payload={"frontend_work_mode": "work", "planner_mode": "model_suggest"}),
        event("assistant_delta", seq=3, run_id="run_work", task_id="task_1", payload={"content": "工作结果"}),
        event("assistant_final", seq=4, run_id="run_work", task_id="task_1", payload={"status": "ok"}),
        event("run_terminal", seq=5, run_id="run_work", task_id="task_1", payload={"status": "ok", "activation_requested": True}),
    ]:
        client2._apply_event(item)  # noqa: SLF001
    snap2 = client2.get_snapshot()
    work_chat = "\n".join(getattr(m, "text", "") for m in snap2.chat_messages)
    assert_true(snap2.active_run_id == "run_work", "work occupies run workbench")
    assert_true("Codex进度" not in work_chat, "workbench events must not pollute chat progress cards")

    bridge = load_bridge_module(root)
    assert_true(
        bridge._classify_execution_error("safecommandrunner: blocked | Code-X工具safecommandrunner已返回结构化结果。[错误分类]模型输出格式错误。", 1, "1ms") == "runtime_tool_blocked",
        "safecommandrunner blocked classified as runtime_tool_blocked before model format",
    )
    assert_true(
        bridge._classify_execution_error("safe_command_runner blocked unsafe_a5_command rm -rf", 1, "1ms") == "a5_command_blocked",
        "safe_command_runner A5 blocked classified as a5_command_blocked",
    )
    d_chat = bridge._runtime_directives_from_payload({"message": "你会做什么", "work_mode": {"mode": "chat", "planner_allowed": True, "tools_requested": True, "long_chain_requested": True}})
    assert_true(not d_chat["tools_requested"] and d_chat["frontend_work_mode"] == "chat", "bridge clamps chat task flags")
    d_work = bridge._runtime_directives_from_payload({"message": "修复 bug", "work_mode": {"mode": "work", "activation_requested": True}})
    assert_true(d_work["task_mode"] == "tool_task" and d_work["activation_requested"] and d_work["llm_fills_activation_form"] and not d_work["tools_requested"], "bridge work route should enter pre-activation chain without forcing tools")
    d_chain = bridge._runtime_directives_from_payload({"message": "修复 bug", "work_mode": {"mode": "long_chain", "activation_requested": True}})
    assert_true(d_chain["frontend_work_mode"] == "work" and d_chain["activation_requested"] and not d_chain["tools_requested"], "bridge legacy long_chain aliases to pre-activation work")

    main_window = (root / "frontend" / "linyuanzhe_frontend" / "ui" / "main_window.py").read_text(encoding="utf-8")
    chat_runtime = (root / "frontend" / "linyuanzhe_frontend" / "ui" / "main_window_chat_runtime.py").read_text(encoding="utf-8")
    feature_pages = (root / "frontend" / "linyuanzhe_frontend" / "ui" / "main_window_feature_pages.py").read_text(encoding="utf-8")
    assert_true("show_task_flow_var" in main_window and "show_task_flow" in main_window, "show task flow preference persisted")
    assert_true("_show_task_flow_enabled" in chat_runtime and "_is_task_flow_progress_message" in chat_runtime, "chat UI gates task flow display")
    assert_true("显示任务流程" in feature_pages, "settings toggle visible")

    print("L6.72.52 task_flow_toggle smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
