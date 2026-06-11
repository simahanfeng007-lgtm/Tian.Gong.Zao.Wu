from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import importlib.util
from pathlib import Path

from linyuanzhe_frontend.clients.sse_runtime_client import (
    SseRuntimeClient,
    extract_host_paths_from_text,
    runtime_submission_text,
)
from linyuanzhe_frontend.contracts.runtime_snapshot import safe_chat_text
from linyuanzhe_frontend.contracts.work_modes import resolve_submit_work_mode, sanitize_work_mode_payload


def assert_true(name: str, value: bool) -> None:
    if not value:
        raise AssertionError(name)


def assert_false(name: str, value: bool) -> None:
    if value:
        raise AssertionError(name)


def assert_eq(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected={expected!r} actual={actual!r}")


def main() -> None:
    win_path = r"C:\Users\User\Desktop\天宫造物\成都新能源货车租赁·抖音运营执行方案（优化版）.txt"
    mac_path = "/Users/user/Desktop/天宫造物/demo file.txt"
    linux_path = "/home/user/天工造物/demo.md"

    # 1. 双模式：chat 不触发工具；work 触发 ActivationForm。旧 code/file/long_chain 只 alias 到 work。
    chat_payload0 = sanitize_work_mode_payload(resolve_submit_work_mode("chat", "请看看这个路径：" + mac_path))
    assert_false("chat_planner_not_allowed", chat_payload0["planner_allowed"])
    assert_false("chat_tools_not_requested", chat_payload0["tools_requested"])
    for mode in ("work", "code", "file", "long_chain"):
        payload0 = sanitize_work_mode_payload(resolve_submit_work_mode(mode, "开始完整验收并打包"))
        assert_eq(f"{mode}_aliases_to_work", payload0["mode"], "work")
        assert_true(f"{mode}_planner_allowed", payload0["planner_allowed"])
        assert_true(f"{mode}_activation_requested", payload0["activation_requested"])
        assert_false(f"{mode}_not_user_long_chain", payload0["long_chain_requested"])

    # 2. Runtime 提交保留 raw 路径；显示层仍可脱敏。
    combined = f"Windows={win_path}\nMac={mac_path}\nLinux={linux_path}"
    assert_eq("runtime_submission_keeps_raw", runtime_submission_text(combined), combined)
    paths = extract_host_paths_from_text(combined)
    assert_true("extract_windows_path", any("C:\\Users\\User" in item for item in paths))
    assert_true("extract_macos_path", any("/Users/user/Desktop" in item for item in paths))
    assert_true("extract_linux_path", any("/home/user" in item for item in paths))
    assert_true("display_redacts_paths", "<redacted>" in safe_chat_text(combined, 1000))

    client = SseRuntimeClient("http://127.0.0.1:8787")
    chat_payload = sanitize_work_mode_payload(resolve_submit_work_mode("chat", combined))
    body = client._chat_payload(combined, work_mode_payload=chat_payload)
    for key in ("message", "user_message", "raw_user_text", "text_raw", "original_user_message"):
        assert_eq(f"payload_{key}_raw", body[key], combined)
        assert_false(f"payload_{key}_no_redacted", "<redacted>" in body[key].lower())
    assert_true("payload_has_path_candidates", len(body.get("host_path_candidates", [])) >= 3)
    assert_true("payload_display_redacted", "<redacted>" in body["message_display"].lower())
    assert_false("chat_payload_planner_false", body["planner_allowed"])
    assert_eq("chat_payload_tool_mode_disabled", body["tool_execution_mode"], "disabled")

    try:
        client._chat_payload("<redacted>", work_mode_payload=chat_payload)
    except RuntimeError as exc:
        assert_true("redacted_guard_error", "path_redaction_leak_detected" in str(exc))
    else:
        raise AssertionError("redacted_guard_missing")

    # 3. 普通聊天连接失败不生成任务工作台，不把诊断原文放入主会话。
    client._active_task_flow = False
    client._active_user_message = "你会做什么"
    snap = client._connection_failure_snapshot("/chat/stream-events 连接失败：RuntimeBackendSubprocess stdout safecommandrunner")
    assert_eq("ordinary_failure_status", snap.current_task_status, "CHATTING")
    assert_eq("ordinary_workbench_idle", snap.run_workbench_state, "idle")
    assert_eq("ordinary_no_run", snap.active_run_id, "")
    visible = "\n".join(str(getattr(item, "text", "")) for item in snap.chat_messages[-3:])
    assert_false("ordinary_no_raw_tool_visible", "safecommandrunner" in visible.lower() or "runtimebackendsubprocess" in visible.lower() or "/chat/stream-events" in visible.lower())

    # 4. 长链连接失败仍进入可恢复任务状态。
    client2 = SseRuntimeClient("http://127.0.0.1:8787")
    client2._active_task_flow = True
    snap2 = client2._connection_failure_snapshot("timeout")
    assert_eq("long_failure_status", snap2.current_task_status, "DISCONNECTED")
    assert_eq("long_failure_workbench", snap2.run_workbench_state, "recoverable")

    # 5. macOS 桌面表面源码级验收：固定侧栏、Label 导航、禁用 macOS 自适应白条路径。
    package_root = Path(__file__).resolve().parents[2]
    main_window = package_root / "frontend" / "linyuanzhe_frontend" / "ui" / "main_window.py"
    theme = package_root / "frontend" / "linyuanzhe_frontend" / "ui" / "theme.py"
    source = main_window.read_text(encoding="utf-8")
    theme_source = theme.read_text(encoding="utf-8")
    assert_true("macos_surface_helper", "def _is_macos_surface" in source)
    assert_true("macos_no_adaptive_sidebar", "macOS 不进入窄侧栏自适应" in source)
    assert_true("sidebar_grid_nsew", 'side.grid(row=1, column=0, sticky="nsew")' in source)
    assert_true("label_navigation", "btn = tk.Label(" in source and "btn.bind(\"<Button-1>\"" in source)
    assert_true("content_min_width", '"content_min_w": 640' in theme_source)
    assert_true("sidebar_fixed_width", '"sidebar_w": 132' in theme_source)

    # 6. 历史页只读回放不写新历史。
    actions = (package_root / "frontend" / "linyuanzhe_frontend" / "ui" / "main_window_actions.py").read_text(encoding="utf-8")
    assert_true("history_readonly_persist_guard", "local_history_readonly" in actions and "历史页是只读回放" in actions)

    # 7. 本地桥接优先读取 raw_user_text，并继续执行“非长链无 run_id”口径。
    bridge_path = package_root / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"
    spec = importlib.util.spec_from_file_location("linyuanzhe_bridge_l67249", bridge_path)
    assert_true("bridge_spec", spec is not None and spec.loader is not None)
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    directives = bridge._runtime_directives_from_payload({
        "message": "<redacted>",
        "raw_user_text": mac_path,
        "frontend_work_mode": "chat",
        "long_chain_requested": True,
        "work_mode": {"mode": "chat", "long_chain_requested": False},
    })
    assert_eq("bridge_chat_not_long_chain", directives["long_chain_requested"], False)
    assert_eq("bridge_chat_planner_false", directives["planner_allowed"], False)

    print("L6.72.52 CrossPlatformLauncherAndGuiAcceptance smoke: PASS")


if __name__ == "__main__":
    main()
