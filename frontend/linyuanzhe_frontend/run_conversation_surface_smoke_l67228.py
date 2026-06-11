from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = ROOT / "frontend"
if str(FRONTEND_ROOT) not in sys.path:
    sys.path.insert(0, str(FRONTEND_ROOT))

from linyuanzhe_frontend.contracts.work_modes import is_casual_chat_message, resolve_submit_work_mode  # noqa: E402
from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient  # noqa: E402


def require(cond: bool, message: str) -> None:
    if not cond:
        raise AssertionError(message)


def load_bridge_module():
    bridge_path = ROOT / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"
    spec = importlib.util.spec_from_file_location("linyuanzhe_local_runtime_bridge_l671", bridge_path)
    require(spec is not None and spec.loader is not None, "bridge spec must load")
    module = importlib.util.module_from_spec(spec)
    sys.modules["linyuanzhe_local_runtime_bridge_l671"] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    require(is_casual_chat_message("在不"), "在不 should be treated as casual chat helper")
    payload = resolve_submit_work_mode("代码", "在不")
    require(payload["effective_mode"] == "work", "legacy code button aliases to work; LLM decides whether it is chat")
    require(payload["activation_requested"] is True and payload["llm_fills_activation_form"] is True, "work mode must request LLM ActivationForm")

    chat_payload = resolve_submit_work_mode("聊天", "修复这个 bug 并运行测试")
    require(chat_payload["effective_mode"] == "chat", "chat mode must not auto-promote")
    require(chat_payload["planner_allowed"] is False and chat_payload["tools_requested"] is False, "chat must not request planner/tools")
    work_payload = resolve_submit_work_mode("工作", "修复这个 bug 并运行测试")
    require(work_payload["effective_mode"] == "work", "explicit work should enter ActivationForm path")
    require(work_payload["planner_allowed"] is True and work_payload["tools_requested"] is True, "work should request planner/tools after LLM activation")

    bridge = load_bridge_module()
    d_chat = bridge._runtime_directives_from_payload({"message": "在不", "frontend_work_mode": "chat", "work_mode": {"mode": "chat"}})
    require(d_chat["frontend_work_mode"] == "chat" and not d_chat["tools_requested"], "bridge chat must stay chat")
    d_work = bridge._runtime_directives_from_payload({"message": "在不", "frontend_work_mode": "work", "work_mode": {"mode": "work", "activation_requested": True}})
    require(d_work["frontend_work_mode"] == "work" and d_work["activation_requested"] is True, "bridge must not keyword-clamp work; LLM decides")
    require(d_work["llm_fills_activation_form"] is True, "bridge must expose ActivationForm boundary")

    cleaned = bridge._clean_user_facing_answer("- return_analysis: ok｜User message appears incomplete: '在不'. Awaiting complete task description.", "在不")
    require(cleaned == "在。", "casual internal return_analysis leak should become normal chat response")
    cleaned_task = bridge._clean_user_facing_answer("- return_analysis: ok｜已完成分析。", "分析下这个问题")
    require("return_analysis" not in cleaned_task and cleaned_task.strip(), "return_analysis prefix should be stripped or hidden")

    client = SseRuntimeClient("http://127.0.0.1:8787")
    client._active_user_message = "在不"
    visible = client._clean_assistant_visible_content("- return_analysis: ok｜User message appears incomplete: '在不'.", final=True)
    require("return_analysis" not in visible and visible.strip(), "SSE visible content should hide return_analysis leak")

    print("L6.72.52 conversation_surface_smoke PASS")


if __name__ == "__main__":
    main()
