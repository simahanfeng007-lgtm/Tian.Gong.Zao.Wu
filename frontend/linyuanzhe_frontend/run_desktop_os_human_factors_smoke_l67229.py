from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = ROOT / "frontend"
if str(FRONTEND_ROOT) not in sys.path:
    sys.path.insert(0, str(FRONTEND_ROOT))

from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION, PROVIDER_CONFIG_SCHEMA_VERSION  # noqa: E402
from linyuanzhe_frontend.contracts.desktop_os_human_factors import audit_capability_flags, default_expected_flags  # noqa: E402
from linyuanzhe_frontend.contracts.work_modes import resolve_submit_work_mode, is_casual_chat_message, WORK_MODE_SPECS  # noqa: E402
from linyuanzhe_frontend.contracts.run_workbench import RUN_STATE_LABELS, ACTIVE_STATES  # noqa: E402
from linyuanzhe_frontend.contracts.streaming_render import streaming_policy  # noqa: E402
from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient  # noqa: E402
from linyuanzhe_frontend.ui.widgets import Card  # noqa: E402
from linyuanzhe_frontend.ui.main_window_chat_runtime import ChatRuntimeMixin  # noqa: E402
from linyuanzhe_frontend.ui.main_window_actions import FrontendActionsMixin  # noqa: E402


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> None:
    require((FE_RUNTIME_VERSION.startswith(("L6.72.", "L6.73.")) or FE_RUNTIME_VERSION.startswith("L6.73.")), "frontend version must be bumped to L6.72.52")
    require(PROVIDER_CONFIG_SCHEMA_VERSION.startswith("tiangong.l6_73_") or PROVIDER_CONFIG_SCHEMA_VERSION.endswith(("l6_72_52.local_provider_config.v1", "l6_73_5.local_provider_config.v1")), "provider schema must accept L6.72.52+ / L6.73.x")

    labels = [spec.label for spec in WORK_MODE_SPECS]
    require(labels == ["聊天", "工作"], f"two-mode labels mismatch: {labels}")
    require(resolve_submit_work_mode("聊天", "修复 bug 并运行测试")["planner_allowed"] is False, "chat mode must not request planner")
    work_payload = resolve_submit_work_mode("工作", "修复 bug 并运行测试")
    require(work_payload["effective_mode"] == "work", "explicit work should enter activation chain")
    require(work_payload["planner_allowed"] is True and work_payload["tools_requested"] is True, "explicit work should enable planner/tools after LLM activation")
    require(resolve_submit_work_mode("代码", "在不")["effective_mode"] == "work", "legacy code aliases to work; LLM may fill chat after ActivationForm")
    require(is_casual_chat_message("在不"), "casual ping helper missing")

    client = SseRuntimeClient("http://127.0.0.1:8787")
    require(client.timeout >= 900.0, "SSE timeout too short for desktop tasks")
    require(client.max_reconnects >= 3, "SSE reconnect budget too low")
    client._active_user_message = "在不"
    require(client._clean_assistant_visible_content("- return_analysis: ok｜User message appears incomplete", final=True) == "刚刚有内部诊断信息被挡在显示层了。现在按普通聊天继续。", "internal return_analysis leak guard failed")
    body = client._chat_payload("修复并打包", work_mode_payload=resolve_submit_work_mode("工作", "修复并打包"))
    require(body["frontend_contract"] == FE_RUNTIME_VERSION, "chat payload version mismatch")
    require(body["frontend_work_mode"] == "work", "work payload should serialize as work")
    require(body["no_frontend_tool_execution"] is True and body["no_frontend_memory_write"] is True, "frontend authority boundary missing")

    require("waiting_approval" in RUN_STATE_LABELS and "tool_running" in RUN_STATE_LABELS, "run state visibility missing")
    require("tool_running" in ACTIVE_STATES and "streaming" in ACTIVE_STATES, "active run states missing")
    policy = streaming_policy()
    require(policy["recommended_flush_interval_ms"] <= 45, "stream rendering flush should stay responsive")
    require(policy["frontend_execution_permission"] == "none", "stream renderer must not execute")

    card_src = inspect.getsource(Card.__init__)
    require("show_subtitle" in card_src and "False" in card_src, "card subtitles should be suppressed by default")
    chat_src = inspect.getsource(ChatRuntimeMixin._build_chat_page)
    require("current_width >= 1360" in chat_src and "_chat_side_panel_visible" in chat_src, "chat side rail should be responsive")
    require(hasattr(ChatRuntimeMixin, "_chat_dynamic_margins"), "chat dynamic margins missing")
    actions_src = inspect.getsource(FrontendActionsMixin._send_message_from_event)
    require("_is_ime_composing_event" in actions_src, "IME Enter guard missing")

    audit = audit_capability_flags(default_expected_flags())
    require(audit["ok"] is True and audit["frontend_executes_tools"] is False, "desktop human-factors audit contract failed")
    print("L6.72.52 desktop_os_human_factors_smoke PASS")


if __name__ == "__main__":
    main()
