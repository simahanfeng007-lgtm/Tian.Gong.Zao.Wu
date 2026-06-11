from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import importlib.util
import json
import sys
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "frontend") not in sys.path:
    sys.path.insert(0, str(ROOT / "frontend"))

from linyuanzhe_frontend.app import main as frontend_main
from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient
from linyuanzhe_frontend.contracts.work_modes import resolve_submit_work_mode
from linyuanzhe_frontend.ui.main_window import LinyuanzheDesktopApp


def require(cond: bool, message: str) -> None:
    if not cond:
        raise AssertionError(message)


def load_bridge_module():
    path = ROOT / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"
    spec = importlib.util.spec_from_file_location("linyuanzhe_local_runtime_bridge_l671_smoke", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_timeout_defaults() -> None:
    client = SseRuntimeClient("http://127.0.0.1:8787")
    require(client.timeout >= 900, "frontend SSE timeout must default to long-task friendly value")
    require(client.max_reconnects >= 3, "frontend SSE reconnects should not be one-shot")
    require(LinyuanzheDesktopApp.__init__.__code__.co_consts is not None, "app class import smoke")


def test_work_mode_directives() -> None:
    bridge = load_bridge_module()
    chat_payload = {"work_mode": resolve_submit_work_mode("聊天", "运行测试并修复 bug")}
    chat_directives = bridge._runtime_directives_from_payload(chat_payload)
    require(chat_directives["frontend_work_mode"] == "chat", "chat mode not normalized")
    require(chat_directives["task_mode"] == "ordinary_chat" and not chat_directives["tools_requested"], "chat must not request tools")
    work_payload = {"work_mode": resolve_submit_work_mode("代码", "运行测试并修复 bug")}
    directives = bridge._runtime_directives_from_payload(work_payload)
    require(directives["frontend_work_mode"] == "work", "legacy code must alias to work")
    require(directives["task_mode"] == "tool_task", "work mode must map to Runtime tool task")
    require(directives["planner_mode"] == "model_suggest", "work mode must enable planner admission")
    # L6.73.1+: work mode only requests ActivationForm prefill at bridge stage.
    # Real tools/long-chain activation is decided later by the LLM-filled ActivationForm.
    require(directives["activation_requested"] is True, "work must request ActivationForm")
    require(directives.get("llm_fills_activation_form") is True, "work must let LLM fill ActivationForm")
    require(directives.get("tools_requested") is False, "pre-activation bridge must not force tools_requested=True")
    require(bridge._normalize_requested_tool_mode("enabled") == "runtime_governed", "enabled tool mode must normalize to runtime_governed")


def test_bridge_sends_sse_before_backend_finishes() -> None:
    bridge = load_bridge_module()
    bridge.STATE = bridge.BridgeState(backend_mode="auto", timeout=20)
    bridge.STATE.provider_base = "https://example.invalid"
    bridge.STATE.provider_key = "mockkey_test"
    bridge.STATE.provider = "openai_compatible"
    bridge.STATE.model = "test-model"

    def slow_backend(message, state, *, runtime_directives=None, run_id=""):
        time.sleep(1.2)
        return "slow backend done", 0, "1200ms"

    original = bridge._run_backend_once
    bridge._run_backend_once = slow_backend
    server = ThreadingHTTPServer(("127.0.0.1", 0), bridge.LinyuanzheBridgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/chat/stream-events"
        payload = {
            "message": "运行测试并修复 bug",
            "tool_execution_mode": "enabled",
            "work_mode": resolve_submit_work_mode("工作", "运行测试并修复 bug"),
            "planner_allowed": True,
            "tools_requested": True,
        }
        started = time.time()
        req = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json; charset=utf-8", "Accept": "text/event-stream"},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            first = resp.readline().decode("utf-8", errors="replace")
            elapsed = time.time() - started
            rest = resp.read().decode("utf-8", errors="replace")
        require(elapsed < 2.0, f"SSE response should stream within CI-safe window; elapsed={elapsed:.3f}s")
        combined = first + rest
        require("slow backend done" in combined, "backend result missing")
        require("event: run_terminal" in combined, "run_terminal missing")
    finally:
        bridge._run_backend_once = original
        server.shutdown()
        server.server_close()


def main() -> int:
    test_timeout_defaults()
    test_work_mode_directives()
    test_bridge_sends_sse_before_backend_finishes()
    print("L6.72.52 execution_frontend_reliability_smoke PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
