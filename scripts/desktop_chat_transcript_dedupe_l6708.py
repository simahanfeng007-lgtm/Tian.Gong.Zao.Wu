from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
if str(FRONTEND) not in sys.path:
    sys.path.insert(0, str(FRONTEND))

from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot, ChatMessage
from linyuanzhe_frontend.clients.mock_runtime_client import MockRuntimeClient


def _count(snapshot: RuntimeSnapshot, text: str) -> int:
    return sum(1 for item in snapshot.chat_messages if text in item.text)


def main() -> int:
    snapshot = RuntimeSnapshot()

    snapshot.submit_confirmation("TICKET-DEDUPE", "approve")
    snapshot.submit_confirmation("TICKET-DEDUPE", "approve")
    assert _count(snapshot, "确认票据 TICKET-DEDUPE") == 1, "confirmation frontend fallback duplicated"

    snapshot.submit_self_iteration_confirmation("CAND-DEDUPE", "approve")
    snapshot.submit_self_iteration_confirmation("CAND-DEDUPE", "approve")
    assert _count(snapshot, "自我迭代候选 CAND-DEDUPE") == 1, "self-iteration frontend fallback duplicated"

    runtime_notice = ChatMessage("assistant", "临渊者", "确认", "确认请求已提交 Runtime 网关；等待 QualityGate/Audit 回执，不由前端放行。")
    snapshot.append_chat_message_once(runtime_notice, "确认请求已提交 Runtime 网关")
    snapshot.append_chat_message_once(runtime_notice, "确认请求已提交 Runtime 网关")
    assert _count(snapshot, "确认请求已提交 Runtime 网关") == 1, "runtime submitted notice duplicated"

    hook_notice = ChatMessage("assistant", "临渊者", "确认", "HookBus 阻断确认请求：blocked-for-test")
    snapshot.append_chat_message_once(hook_notice, "HookBus 阻断确认请求", "blocked-for-test")
    snapshot.append_chat_message_once(hook_notice, "HookBus 阻断确认请求", "blocked-for-test")
    assert _count(snapshot, "HookBus 阻断确认请求") == 1, "HookBus confirmation notice duplicated"

    client = MockRuntimeClient()
    client.submit_user_message("refresh-preserve-user-message")
    before = [item.text for item in client.get_snapshot().chat_messages]
    client.refresh_snapshot()
    after = [item.text for item in client.get_snapshot().chat_messages]
    assert any("refresh-preserve-user-message" in item for item in before), "test setup failed"
    assert any("refresh-preserve-user-message" in item for item in after), "mock refresh discarded accumulated transcript"

    print("desktop_chat_transcript_dedupe_l6708: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
