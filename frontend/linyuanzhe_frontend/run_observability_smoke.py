from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient
from linyuanzhe_frontend.contracts.observability import OBSERVABILITY_CONTRACT_VERSION, TraceRecord, TraceStats, observability_policy
from linyuanzhe_frontend.contracts.sse_events import RuntimeSseEvent


def _assert(cond: bool, message: str) -> None:
    if not cond:
        raise AssertionError(message)


def main(argv: list[str] | None = None) -> int:
    client = SseRuntimeClient("http://127.0.0.1:8787")
    events = [
        RuntimeSseEvent(event="run_started", seq=1, run_id="run-l662", task_id="tamockkey_l662", payload={"status": "running", "latency_ms": 12}),
        RuntimeSseEvent(event="planner_started", seq=2, run_id="run-l662", task_id="tamockkey_l662", payload={"planner_mode": "unified"}),
        RuntimeSseEvent(event="planner_plan", seq=3, run_id="run-l662", task_id="tamockkey_l662", payload={"steps": [{"tool_name": "readonly_probe", "status": "queued"}]}),
        RuntimeSseEvent(event="quality_gate", seq=4, run_id="run-l662", task_id="tamockkey_l662", payload={"risk_level": "A5", "decision": "confirmation_required", "gate_id": "gate-l662", "audit_ref": "audit-l662", "action_summary": "只读观测测试"}),
        RuntimeSseEvent(event="tool_started", seq=5, run_id="run-l662", task_id="tamockkey_l662", payload={"tool_name": "readonly_probe"}),
        RuntimeSseEvent(event="tool_result", seq=6, run_id="run-l662", task_id="tamockkey_l662", payload={"tool_name": "readonly_probe", "status": "ok", "audit_ref": "audit-l662", "output_summary": "只读探测完成"}),
        RuntimeSseEvent(event="audit_event", seq=7, run_id="run-l662", task_id="tamockkey_l662", payload={"audit_id": "audit-l662", "message": "审计只读投影"}),
        RuntimeSseEvent(event="runtime_state", seq=8, run_id="run-l662", task_id="tamockkey_l662", payload={"status": "RUNNING", "provider_base_url_configured": True, "provider_base_url_digest": "digest_example_runtime", "authorization_configured": True, "authorization_digest": "digest_token_marker"}),
        RuntimeSseEvent(event="assistant_final", seq=9, run_id="run-l662", task_id="tamockkey_l662", payload={"status": "ok", "content": "观测台 smoke 完成"}),
        RuntimeSseEvent(event="run_terminal", seq=10, run_id="run-l662", task_id="tamockkey_l662", payload={"status": "ok"}),
    ]
    for event in events:
        client._apply_event(event)
    snap = client.get_snapshot()
    stats = dict(snap.trace_stats)
    _assert(snap.observability_contract == OBSERVABILITY_CONTRACT_VERSION, "observability contract mismatch")
    _assert(stats.get("total_events") == len(events), "trace event count mismatch")
    _assert(stats.get("tool_events") == 2, "tool event count mismatch")
    _assert(stats.get("quality_gate_events") == 1, "quality gate count mismatch")
    _assert(stats.get("audit_events") == 1, "audit event count mismatch")
    _assert(stats.get("assistant_events") == 1, "assistant event count mismatch")
    _assert(stats.get("terminal_events") == 1, "terminal event count mismatch")
    _assert(bool(stats.get("terminal_order_valid")), "terminal order should be valid")
    _assert(bool(snap.trace_export_digest), "trace export digest missing")
    text = json.dumps(snap.to_dict(), ensure_ascii=False)
    _assert("provider_base_url" not in text.lower() or "configured" in text.lower(), "raw endpoint field leaked into trace projection")
    _assert("token_marker_not_secret" not in text, "raw auth marker leaked into trace projection")
    bad_records = [
        TraceRecord(seq=1, source_event="run_terminal", event_type="run_terminal", category="terminal", terminal=True),
        TraceRecord(seq=2, source_event="assistant_final", event_type="assistant_final", category="assistant"),
    ]
    _assert(not TraceStats.from_records(bad_records).terminal_order_valid, "bad terminal order not detected")
    payload = {
        "ok": True,
        "contract": snap.observability_contract,
        "stats": stats,
        "policy": observability_policy(),
        "trace_export_digest": snap.trace_export_digest,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
