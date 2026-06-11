from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



from linyuanzhe_frontend.contracts.work_modes import (
    WORK_MODE_CONTRACT_VERSION,
    infer_work_mode_from_text,
    resolve_submit_work_mode,
    work_mode_labels,
)
from linyuanzhe_frontend.clients.mock_runtime_client import MockRuntimeClient
from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient
from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    labels = work_mode_labels()
    require(labels == ["聊天", "工作"], f"two-mode labels mismatch: {labels}")

    # L6.72.52：前端不再用关键词/后缀识别 code/file/document/long_chain，真实裁决由 LLM 填 ActivationForm。
    for text in ("修复这个包然后给我 zip", "运行 compileall 并测试代码", "读取文件并导出 JSON", "完整全链验收并打包"):
        require(infer_work_mode_from_text(text) == "chat", "frontend inference must stay neutral")

    chat_payload = resolve_submit_work_mode("聊天", "修复入口并跑测试")
    require(chat_payload["mode"] == "chat", "chat mode must be preserved")
    require(chat_payload["planner_allowed"] is False, "chat mode must not request planner")
    require(chat_payload["tools_requested"] is False, "chat mode must not request tools")
    require(chat_payload["llm_fills_activation_form"] is True, "activation boundary missing")

    work_payload = resolve_submit_work_mode("工作", "继续下一步")
    require(work_payload["mode"] == "work", "work mode not preserved")
    require(work_payload["activation_requested"] is True, "work must request LLM ActivationForm")
    require(work_payload["planner_allowed"] is True, "work should allow planner after LLM activation")
    require(work_payload["tools_requested"] is True, "work should allow tools after LLM activation")
    require(work_payload["long_chain_requested"] is False, "long_chain is not a user mode flag anymore")

    legacy_payload = resolve_submit_work_mode("long_chain", "继续下一步")
    require(legacy_payload["mode"] == "work", "legacy long_chain should alias to work")

    mock = MockRuntimeClient()
    snap = mock.submit_user_message_streaming("修复并测试", work_mode_payload=work_payload)
    require(snap.planner_mode == "work_mode_requested", "mock should record work planner request")
    require(snap.tool_execution_mode == "runtime_governed", "mock should record governed tool mode request")
    require("工作模式" in snap.chat_messages[-1].text, "mock assistant should expose work mode summary")

    client = SseRuntimeClient("http://127.0.0.1:8787")
    body = client._chat_payload("修复并测试", work_mode_payload=work_payload)  # static payload smoke; no network call
    compatible_versions = {"L6.72.52", "L6.73.0", "L6.73.1", "L6.73.2", "L6.73.3", "L6.73.4", "L6.73.5", "L6.73.6", "L6.73.7", "L6.73.8"}
    require(body["frontend_contract"] == FE_RUNTIME_VERSION and (FE_RUNTIME_VERSION in compatible_versions or FE_RUNTIME_VERSION.startswith("L6.73.")), "frontend contract not bumped")
    require(body["work_mode_contract"] == WORK_MODE_CONTRACT_VERSION, "work mode contract missing")
    require(body["frontend_work_mode"] == "work", "frontend work mode not serialized as work")
    require(body["planner_allowed"] is True, "planner flag not serialized")
    require(body["tools_requested"] is True, "tool request flag not serialized")
    require(body["activation_requested"] is True, "activation flag not serialized")
    require(body["no_frontend_tool_execution"] is True, "frontend tool execution boundary missing")
    print("L6.72.52 two_mode_activation_smoke PASS")


if __name__ == "__main__":
    main()
