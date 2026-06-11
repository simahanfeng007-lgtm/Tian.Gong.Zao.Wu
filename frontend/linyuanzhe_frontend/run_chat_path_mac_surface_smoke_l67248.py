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

from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient, runtime_submission_text
from linyuanzhe_frontend.contracts.runtime_snapshot import safe_chat_text
from linyuanzhe_frontend.contracts.work_modes import is_casual_chat_message, resolve_submit_work_mode, sanitize_work_mode_payload


def assert_true(name: str, value: bool) -> None:
    if not value:
        raise AssertionError(name)


def main() -> None:
    win_path = r"C:\Users\User\Desktop\天宫造物\成都新能源货车租赁·抖音运营执行方案（优化版）.txt"
    mac_path = "/Users/user/Desktop/天宫造物/demo.txt"

    assert_true("runtime_submission_keeps_windows_path", runtime_submission_text(win_path) == win_path)
    assert_true("runtime_submission_keeps_macos_path", runtime_submission_text(mac_path) == mac_path)
    assert_true("display_sanitizer_still_redacts_windows_path", "<redacted>" in safe_chat_text(win_path, 1000))
    assert_true("display_sanitizer_still_redacts_macos_path", "<redacted>" in safe_chat_text(mac_path, 1000))

    client = SseRuntimeClient("http://127.0.0.1:8787")
    work_payload = sanitize_work_mode_payload(resolve_submit_work_mode("chat", win_path))
    body = client._chat_payload(win_path, work_mode_payload=work_payload)
    assert_true("payload_message_is_raw", body["message"] == win_path)
    assert_true("payload_user_message_is_raw", body["user_message"] == win_path)
    assert_true("payload_display_is_redacted", "<redacted>" in body["message_display"])
    assert_true("chat_mode_no_planner", body["planner_allowed"] is False and body["tools_requested"] is False)

    assert_true("troubleshooting_question_is_casual", is_casual_chat_message("刚刚什么情况啊"))
    client._active_user_message = "刚刚什么情况啊"
    leaked = "工具: RuntimeBackendSubprocess\nrunstate=completed safecommandrunner buildshellsystemmount\nstdout: <raw>"
    cleaned = client._clean_assistant_visible_content(leaked, final=True)
    assert_true("internal_markers_removed", "safecommandrunner" not in cleaned.lower() and "runstate" not in cleaned.lower())
    assert_true("fallback_visible", "内部诊断信息" in cleaned or cleaned.strip())

    root = Path(__file__).resolve().parents[1]
    main_window = root / "linyuanzhe_frontend" / "ui" / "main_window.py"
    source = main_window.read_text(encoding="utf-8")
    assert_true("mac_sidebar_fixed_width", 'return DIMENS["sidebar_w"]' in source)
    assert_true("mac_icon_threshold", "width < 900" in source)
    assert_true("mac_label_navigation", "btn = tk.Label(" in source and "btn.bind(\"<Button-1>\"" in source)
    assert_true("old_percentage_sidebar_removed", "min(260, int(width * 0.22))" not in source)

    package_root = Path(__file__).resolve().parents[2]
    bridge_path = package_root / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"
    spec = importlib.util.spec_from_file_location("linyuanzhe_local_runtime_bridge_l671_smoke", bridge_path)
    assert_true("desktop_bridge_spec", spec is not None and spec.loader is not None)
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    assert_true("desktop_troubleshooting_chat_is_casual", bridge._is_casual_chat_message("刚刚什么情况啊"))
    bridge_cleaned = bridge._clean_user_facing_answer("runstate=completed safecommandrunner RuntimeBackendSubprocess\nstdout: x", "刚刚什么情况啊")
    assert_true("desktop_internal_markers_removed", "safecommandrunner" not in bridge_cleaned.lower() and "runstate" not in bridge_cleaned.lower())

    print("L6.72.48 chat path / internal leak / mac surface smoke: PASS")


if __name__ == "__main__":
    main()
