from __future__ import annotations

import json

from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient
from linyuanzhe_frontend.contracts.hook_bus import HOOK_BUS_CONTRACT_VERSION, HookBus, hook_bus_policy
from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot
from linyuanzhe_frontend.contracts.sse_events import RuntimeSseEvent


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    policy = hook_bus_policy()
    _assert(policy["no_tool_execution"], "HookBus policy must forbid frontend tool execution")
    _assert(policy["a5_must_block_or_confirm"], "HookBus must enforce A5 confirmation/block semantics")

    hook_bus = HookBus.default_frontend_bus()
    blocked = hook_bus.evaluate("pre_event_apply", {"event": "quality_gate", "payload": {"risk_level": "A5", "decision": "allowed"}})
    _assert(not blocked.ok and blocked.verdict == "block", "A5 allowed event was not blocked")
    missing_flags = hook_bus.evaluate("pre_chat_submit", {"payload": {"message": "hello"}})
    _assert(not missing_flags.ok, "chat payload without safety flags was not blocked")

    client = SseRuntimeClient("http://127.0.0.1:8787", timeout=0.1, max_reconnects=0)
    good_events = [
        RuntimeSseEvent(event="run_started", seq=1, run_id="run-l663", task_id="task-l663", payload={"runtime_status": "active"}),
        RuntimeSseEvent(event="quality_gate", seq=2, run_id="run-l663", task_id="task-l663", payload={"risk_level": "A3", "decision": "allowed", "gate_id": "gate-l663"}),
        RuntimeSseEvent(event="assistant_final", seq=3, run_id="run-l663", task_id="task-l663", payload={"content": "HookBus smoke ok", "status": "ok"}),
        RuntimeSseEvent(event="run_terminal", seq=4, run_id="run-l663", task_id="task-l663", payload={"status": "ok"}),
    ]
    for event in good_events:
        client._apply_event(event)
    client._evaluate_hook("pre_finalize", {"terminal_order_valid": True, "payload": {"event_count": len(good_events)}})
    snap = client.get_snapshot()
    _assert(snap.hook_bus_contract == HOOK_BUS_CONTRACT_VERSION, "HookBus contract mismatch")
    _assert(snap.hook_stats.get("total_hooks", 0) >= 8, "Hook records were not collected")
    _assert(snap.hook_stats.get("block_count", 0) == 0, "good event path should not be blocked")
    _assert(bool(snap.hook_export_digest), "Hook export digest missing")
    _assert(snap.trace_terminal_order_valid, "good terminal order should remain valid")

    bad_client = SseRuntimeClient("http://127.0.0.1:8787", timeout=0.1, max_reconnects=0)
    bad_client._apply_event(RuntimeSseEvent(event="quality_gate", seq=1, run_id="bad-run", task_id="bad-task", payload={"risk_level": "A5", "decision": "allowed", "gate_id": "gate-a5"}))
    bad_snap = bad_client.get_snapshot()
    _assert(bad_snap.current_task_status == "BLOCKED", "A5 allowed event did not set BLOCKED state")
    _assert(bad_snap.hook_stats.get("block_count", 0) >= 1, "A5 block not counted")
    _assert("A5" in bad_snap.gate_status, "A5 hook block not reflected in gate status")

    order_client = SseRuntimeClient("http://127.0.0.1:8787", timeout=0.1, max_reconnects=0)
    order_client._apply_event(RuntimeSseEvent(event="run_terminal", seq=1, run_id="order-run", task_id="order-task", payload={"status": "ok"}))
    order_snap = order_client.get_snapshot()
    _assert(order_snap.current_task_status == "BLOCKED", "terminal order violation did not block")
    _assert(order_snap.hook_stats.get("block_count", 0) >= 1, "terminal order block not counted")

    # Provider settings may carry outbound credential material to Runtime, but
    # HookRecord must keep only configured/digest style summaries.
    provider_payload = {
        "frontend_contract": "tiangong.test",
        "provider": "deepseek",
        "model": "deepseek-v4-pro",
        "api_key": "demo-secret-marker",
        "base_url": "local-runtime-marker",
    }
    provider_decision = hook_bus.evaluate("pre_provider_settings_submit", {"payload": provider_payload})
    _assert(provider_decision.ok, "provider write-only hook unexpectedly blocked valid outbound request")
    provider_text = json.dumps([record.to_dict() for record in hook_bus.records], ensure_ascii=False)
    _assert("demo-secret-marker" not in provider_text, "raw provider secret leaked into HookRecord")
    _assert("local-runtime-marker" not in provider_text, "raw provider endpoint marker leaked into HookRecord")

    runtime_snapshot = RuntimeSnapshot()
    _assert(runtime_snapshot.hook_bus_contract == HOOK_BUS_CONTRACT_VERSION, "RuntimeSnapshot did not expose HookBus contract")
    _assert(runtime_snapshot.hook_records, "RuntimeSnapshot default Hook records missing")

    payload = {
        "ok": True,
        "contract": HOOK_BUS_CONTRACT_VERSION,
        "policy": policy,
        "good_stats": snap.hook_stats,
        "bad_stats": bad_snap.hook_stats,
        "order_stats": order_snap.hook_stats,
        "default_hook_count": len(runtime_snapshot.hook_records),
        "hook_export_digest": snap.hook_export_digest,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
