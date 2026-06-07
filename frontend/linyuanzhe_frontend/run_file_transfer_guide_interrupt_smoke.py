from __future__ import annotations

import json
import tempfile
from dataclasses import asdict
from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient
from linyuanzhe_frontend.contracts.file_transfer import FILE_TRANSFER_CONTRACT_VERSION
from linyuanzhe_frontend.contracts.hook_bus import HOOK_STAGE_PRE_FILE_TRANSFER_REQUEST, HookBus
from linyuanzhe_frontend.scripts.runtime_contract_server import RuntimeContractHandler, RuntimeContractServer


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    hook_bus = HookBus.default_frontend_bus()
    bad_decision = hook_bus.evaluate(
        HOOK_STAGE_PRE_FILE_TRANSFER_REQUEST,
        {"payload": {"file_name": "a.txt", "size_bytes": 1, "sha256": "a" * 64, "raw_content_inline": True}},
    )
    _assert(not bad_decision.ok, "unsafe file transfer payload was not blocked")

    with tempfile.TemporaryDirectory(prefix="l664_file_transfer_") as tmpdir:
        selected = Path(tmpdir) / "用户附件_烟测.txt"
        selected.write_text("L6.64 sanitized file transfer smoke fixture. No secrets here.\n", encoding="utf-8")
        raw_path = str(selected)

        with RuntimeContractServer() as server:
            client = SseRuntimeClient(server.url, timeout=2.0, max_reconnects=0)
            snapshot = client.refresh_snapshot()
            snapshot = client.request_file_transfer(raw_path, "user_attachment")
            records = list(snapshot.file_transfer_records or [])
            _assert(records, "file transfer record missing")
            latest = records[-1]
            _assert(latest.status == "accepted", f"unexpected file transfer status: {latest.status}")
            _assert(latest.file_name == selected.name, "public record lost sanitized file name")
            _assert(latest.audit_id == "audit_l664_file_transfer", "file transfer audit id missing")
            _assert(snapshot.file_transfer_contract == FILE_TRANSFER_CONTRACT_VERSION, "file transfer contract mismatch")
            snapshot_text = json.dumps(snapshot.to_dict(), ensure_ascii=False)
            _assert(raw_path not in snapshot_text, "raw local path leaked into RuntimeSnapshot")
            _assert("L6.64 sanitized file transfer smoke fixture" not in snapshot_text, "raw file content leaked into RuntimeSnapshot")
            _assert(RuntimeContractHandler.file_transfer_payloads, "contract server did not receive transfer payload")
            payload_text = json.dumps(RuntimeContractHandler.file_transfer_payloads[-1], ensure_ascii=False)
            _assert(raw_path not in payload_text, "raw local path leaked into transfer request payload")
            _assert("L6.64 sanitized file transfer smoke fixture" not in payload_text, "raw file content leaked into transfer request payload")
            _assert(RuntimeContractHandler.file_transfer_payloads[-1].get("route_to_runtime_only") is True, "transfer payload did not route to Runtime only")
            _assert(RuntimeContractHandler.file_transfer_payloads[-1].get("no_frontend_tool_execution") is True, "transfer payload missed no frontend tool flag")

            snapshot = client.request_task_interrupt("user_clicked_interrupt_button")
            _assert(snapshot.control_state == "interrupt_accepted", f"unexpected interrupt state: {snapshot.control_state}")
            _assert(RuntimeContractHandler.control_payloads, "interrupt control payload missing")
            _assert(RuntimeContractHandler.control_payloads[-1].get("action") == "interrupt", "wrong control action")
            _assert(RuntimeContractHandler.control_payloads[-1].get("no_frontend_tool_execution") is True, "interrupt payload missed no frontend tool flag")

            guide = snapshot.conversation_guide
            _assert(guide.recommended_actions, "conversation guide recommended_actions missing")
            _assert(guide.suggested_questions, "conversation guide suggested_questions missing")
            _assert(any("中断" in item or "附件" in item or "上传" in item for item in guide.recommended_actions), "conversation guide did not expose L6.64 actions")

            result = {
                "ok": True,
                "contract": FILE_TRANSFER_CONTRACT_VERSION,
                "runtime_url": server.url,
                "file_record": latest.to_dict(),
                "control_state": snapshot.control_state,
                "guide": asdict(guide),
                "raw_path_exposed": False,
                "raw_content_exposed": False,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
