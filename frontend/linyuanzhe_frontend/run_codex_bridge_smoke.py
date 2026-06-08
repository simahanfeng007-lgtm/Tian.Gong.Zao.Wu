from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from linyuanzhe_frontend.clients import RuntimeIntegrationProbe
from linyuanzhe_frontend.contracts.sse_events import parse_sse_bytes, validate_terminal_order
from linyuanzhe_frontend.scripts.runtime_contract_server import RuntimeContractServer


def main() -> int:
    server = RuntimeContractServer().start()
    try:
        probe = RuntimeIntegrationProbe(server.url, timeout=8, mode="contract_server")
        report = probe.run("code-x smoke .")
        payload = report.to_dict()
        # Directly validate Code-X projection path from contract server.
        import urllib.request
        body = json.dumps({"message": "code-x smoke ."}).encode("utf-8")
        req = urllib.request.Request(server.url + "/chat/stream-events", data=body, headers={"Content-Type": "application/json"})
        raw = urllib.request.urlopen(req, timeout=8).read()
        events = parse_sse_bytes(raw)
        tool_names = [e.payload.get("tool_name") for e in events if e.event == "tool_result"]
        payload["code_x_projection_ok"] = "code_x_runtime_status" in tool_names and "repo_map" in tool_names and validate_terminal_order(events)
        payload["code_x_tool_results"] = tool_names
        out = Path(__file__).resolve().parent / "reports" / "l6702_codex_frontend_bridge_smoke_report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        ok = bool(payload.get("ok")) and bool(payload["code_x_projection_ok"])
        print(json.dumps({"ok": ok, "report": str(out), "code_x_tool_results": tool_names}, ensure_ascii=False, indent=2))
        return 0 if ok else 1
    finally:
        server.close()


if __name__ == "__main__":
    raise SystemExit(main())
