"""Q22 verifier: work-mode ordinary questions/analysis must remain chat.

Covers the Windows desktop UX where the mode selector is left at "工作" but the
user asks a natural question such as "为什么会这样啊，我问他话，它给我回复这个".
Those messages must not surface ActivationForm/tool-chain failures.  Concrete
execution requests must still keep the work boundary.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Mapping, Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "project"
FRONTEND = ROOT / "frontend"
for item in (ROOT, BACKEND, FRONTEND):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
os.environ.setdefault("PYTHONNOUSERSITE", "1")
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")
os.environ.setdefault("LINYUANZHE_STATE_DIR", str(Path(tempfile.mkdtemp(prefix="linyuanzhe_q22_state_"))))
os.environ.setdefault("TIANGONG_STATE_DIR", os.environ["LINYUANZHE_STATE_DIR"])
os.environ.setdefault("LINYUANZHE_PROVIDER_CONFIG_FILE", str(Path(tempfile.mkdtemp(prefix="linyuanzhe_q22_cfg_")) / "provider_config.json"))

from desktop import linyuanzhe_local_runtime_bridge_l671 as bridge  # noqa: E402
from frontend.linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient  # noqa: E402
from frontend.linyuanzhe_frontend.contracts.work_modes import (  # noqa: E402
    is_dialogue_or_analysis_message,
    resolve_submit_work_mode,
)


DIALOGUE_CASES = [
    "为什么会这样啊，我问他话，它给我回复这个",
    "这是什么问题？",
    "这个错误是什么意思？",
    "帮我分析一下这个报错",
    "现在这个能做长链工作了？",
    "我这个是不是还没有网关，无法链接微信，飞书",
    "你是谁？",
    "你能做什么？",
    "这个文件为什么打不开？",
]

WORK_CASES = [
    "请检查这个项目，定位 bug，修复并给出总结。",
    "帮我修复 backend/project/foo.py 的 bug",
    r"读取 C:\Users\a\Desktop\test.txt 并总结",
    "把结果打包成 zip",
    "在当前项目里创建 CHANGELOG.txt，内容：hello",
    r"请读取这个文件并总结：C:\Users\a\Desktop\x.txt",
]


def require(name: str, condition: bool, detail: object = "") -> None:
    if not condition:
        raise AssertionError(f"{name} failed" + (f": {detail}" if detail else ""))
    print(f"PASS {name}")


def make_offline_state() -> bridge.BridgeState:
    state = bridge.BridgeState(backend_mode="local", timeout=6)
    state.provider_key = ""
    state.provider_base = ""
    state.provider = "deepseek"
    state.model = "deepseek-chat"
    state.host_access_scope = "project_workspace"
    state.host_access_root = BACKEND
    state.file_handoffs.clear()
    return state


def assert_chat_payload(client: SseRuntimeClient, message: str) -> None:
    require(f"dialogue classifier: {message}", is_dialogue_or_analysis_message(message))
    work_payload = resolve_submit_work_mode("工作", message)
    require(f"frontend overrides work to chat: {message}", work_payload["mode"] == "chat", work_payload)
    require(f"frontend no activation: {message}", work_payload["activation_requested"] is False, work_payload)
    require(f"frontend no tools: {message}", work_payload["tools_requested"] is False, work_payload)
    require(f"frontend dialogue override: {message}", work_payload.get("dialogue_only_override") is True, work_payload)

    body = client._chat_payload(message, work_mode_payload=work_payload)
    require(f"sse submits chat: {message}", body["frontend_work_mode"] == "chat", body)
    require(f"sse disables tool mode: {message}", body["tool_execution_mode"] == "disabled", body)
    require(f"sse no activation: {message}", body["activation_requested"] is False, body)
    require(f"sse no tools: {message}", body["tools_requested"] is False, body)

    directives = bridge._runtime_directives_from_payload(body)
    require(f"bridge directives chat: {message}", directives["frontend_work_mode"] == "chat", directives)
    require(f"bridge no activation: {message}", directives["activation_requested"] is False, directives)
    require(f"bridge no tools: {message}", directives["tools_requested"] is False, directives)
    require(f"bridge dialogue override: {message}", directives.get("dialogue_only_override") is True, directives)

    answer, rc, elapsed = bridge._run_backend_once(message, make_offline_state(), runtime_directives=directives)
    require(f"offline rc zero: {message}", rc == 0, answer)
    require(f"offline local dialogue: {message}", elapsed == "local_dialogue", elapsed)
    require(
        f"no runtime failure visible: {message}",
        "Runtime 工具任务失败" not in answer
        and "主脑本轮未激活工具链" not in answer
        and "本地后端执行失败" not in answer,
        answer,
    )


def assert_work_payload(client: SseRuntimeClient, message: str) -> None:
    require(f"execution classifier false: {message}", not is_dialogue_or_analysis_message(message))
    work_payload = resolve_submit_work_mode("工作", message)
    require(f"real work keeps work mode: {message}", work_payload["mode"] == "work", work_payload)
    require(f"real work keeps activation: {message}", work_payload["activation_requested"] is True, work_payload)
    require(f"real work keeps tools boundary: {message}", work_payload["tools_requested"] is True, work_payload)
    body = client._chat_payload(message, work_mode_payload=work_payload)
    directives = bridge._runtime_directives_from_payload(body)
    require(f"real work bridge mode: {message}", directives["frontend_work_mode"] == "work", directives)
    require(f"real work bridge activation: {message}", directives["activation_requested"] is True, directives)


def assert_legacy_payload_is_protected(message: str) -> None:
    legacy_payload: Mapping[str, Any] = {
        "message": message,
        "frontend_work_mode": "work",
        "activation_requested": True,
        "tools_requested": True,
        "work_mode": {
            "mode": "work",
            "activation_requested": True,
            "tools_requested": True,
            "llm_fills_activation_form": True,
        },
    }
    directives = bridge._runtime_directives_from_payload(legacy_payload)
    require("legacy forced work analysis becomes chat", directives["frontend_work_mode"] == "chat", directives)
    require("legacy forced work analysis no activation", directives["activation_requested"] is False, directives)
    require("legacy forced work analysis no tools", directives["tools_requested"] is False, directives)
    answer, rc, elapsed = bridge._run_backend_once(message, make_offline_state(), runtime_directives=directives)
    require("legacy forced work analysis rc zero", rc == 0, answer)
    require("legacy forced work analysis local fallback", elapsed == "local_dialogue", elapsed)
    require("legacy forced work analysis no visible runtime failure", "Runtime 工具任务失败" not in answer and "主脑本轮未激活工具链" not in answer, answer)


def main() -> int:
    client = SseRuntimeClient("http://127.0.0.1:9")
    for message in DIALOGUE_CASES:
        assert_chat_payload(client, message)
    for message in WORK_CASES:
        assert_work_payload(client, message)
    assert_legacy_payload_is_protected("为什么会这样啊，我问他话，它给我回复这个")
    assert_legacy_payload_is_protected("这个错误是什么意思？")
    print("PASS Q22 dialogue/analysis work-mode boundary verifier")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
