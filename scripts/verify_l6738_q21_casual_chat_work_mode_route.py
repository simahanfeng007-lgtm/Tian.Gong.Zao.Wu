"""Q21 verifier: casual chat must not enter work/tool failure route.

This covers the Windows desktop case where the user keeps the bottom-left mode
selector on "工作" but asks a casual question such as "忙呢？".  The frontend
must submit it as ordinary chat, and the bridge must have a local fallback for
legacy work payloads so the user never sees Runtime tool-task failure text.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "project"
FRONTEND = ROOT / "frontend"
for item in (ROOT, BACKEND, FRONTEND):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
os.environ.setdefault("PYTHONNOUSERSITE", "1")
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")
os.environ.setdefault("LINYUANZHE_STATE_DIR", str(Path(tempfile.mkdtemp(prefix="linyuanzhe_q21_state_"))))
os.environ.setdefault("TIANGONG_STATE_DIR", os.environ["LINYUANZHE_STATE_DIR"])
os.environ.setdefault("LINYUANZHE_PROVIDER_CONFIG_FILE", str(Path(tempfile.mkdtemp(prefix="linyuanzhe_q21_cfg_")) / "provider_config.json"))

from desktop import linyuanzhe_local_runtime_bridge_l671 as bridge  # noqa: E402
from frontend.linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient  # noqa: E402
from frontend.linyuanzhe_frontend.contracts.work_modes import (  # noqa: E402
    is_casual_chat_message,
    resolve_submit_work_mode,
)


def require(name: str, condition: bool, detail: object = "") -> None:
    if not condition:
        raise AssertionError(f"{name} failed" + (f": {detail}" if detail else ""))
    print(f"PASS {name}")


def make_offline_state() -> bridge.BridgeState:
    state = bridge.BridgeState(backend_mode="local", timeout=8)
    state.provider_key = ""
    state.provider_base = ""
    state.provider = "deepseek"
    state.model = "deepseek-chat"
    state.host_access_scope = "project_workspace"
    state.host_access_root = BACKEND
    state.file_handoffs.clear()
    return state


def main() -> int:
    # 1. The exact user screenshot case is now classified as casual chat.
    require("frontend recognizes 忙呢", is_casual_chat_message("忙呢？"))

    casual_payload = resolve_submit_work_mode("工作", "忙呢？")
    require("work+casual effective chat", casual_payload["mode"] == "chat", casual_payload)
    require("work+casual override flag", casual_payload.get("casual_chat_override") is True, casual_payload)
    require("work+casual no activation", casual_payload["activation_requested"] is False, casual_payload)
    require("work+casual no planner", casual_payload["planner_allowed"] is False, casual_payload)
    require("work+casual no tools", casual_payload["tools_requested"] is False, casual_payload)

    client = SseRuntimeClient("http://127.0.0.1:9")
    body = client._chat_payload("忙呢？", work_mode_payload=casual_payload)
    require("sse body submits chat", body["frontend_work_mode"] == "chat", body)
    require("sse body disables tool mode", body["tool_execution_mode"] == "disabled", body)
    require("sse body no activation", body["activation_requested"] is False, body)
    require("sse body no tools", body["tools_requested"] is False, body)

    directives = bridge._runtime_directives_from_payload(body)
    require("bridge directives chat", directives["frontend_work_mode"] == "chat", directives)
    require("bridge directives no activation", directives["activation_requested"] is False, directives)
    require("bridge directives no tools", directives["tools_requested"] is False, directives)

    state = make_offline_state()
    answer, rc, elapsed = bridge._run_backend_once("忙呢？", state, runtime_directives=directives)
    require("offline casual rc zero", rc == 0, answer)
    require("offline casual friendly answer", "不忙" in answer or answer.strip() == "在。", answer)
    require("offline casual local fallback", elapsed == "local_dialogue", elapsed)
    require("offline casual no runtime failure", "Runtime 工具任务失败" not in answer and "主脑本轮未激活工具链" not in answer, answer)

    # 2. Legacy forced work payloads are also protected at bridge boundary.
    legacy_payload = {
        "message": "忙呢？",
        "work_mode": {
            "mode": "work",
            "activation_requested": True,
            "tools_requested": True,
            "llm_fills_activation_form": True,
        },
    }
    legacy_directives = bridge._runtime_directives_from_payload(legacy_payload)
    legacy_answer, legacy_rc, legacy_elapsed = bridge._run_backend_once("忙呢？", make_offline_state(), runtime_directives=legacy_directives)
    require("legacy forced work casual rc zero", legacy_rc == 0, legacy_answer)
    require("legacy forced work no visible runtime failure", "Runtime 工具任务失败" not in legacy_answer and "主脑本轮未激活工具链" not in legacy_answer, legacy_answer)
    require("legacy forced work local fallback", legacy_elapsed == "local_dialogue", legacy_elapsed)

    # 3. Real work instructions still preserve work activation boundary.
    work_payload = resolve_submit_work_mode("工作", "请检查这个项目，定位 bug，修复并给出总结。")
    require("real work keeps mode", work_payload["mode"] == "work", work_payload)
    require("real work keeps activation", work_payload["activation_requested"] is True, work_payload)
    require("real work keeps tools boundary", work_payload["tools_requested"] is True, work_payload)

    print("PASS Q21 casual chat work-mode route verifier")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
