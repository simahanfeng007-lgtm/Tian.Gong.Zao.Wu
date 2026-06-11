from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import json
import re

from linyuanzhe_frontend.clients.mock_runtime_client import MockRuntimeClient
from linyuanzhe_frontend.contracts.connectors import ConnectorRegistrationRequest, connector_registry_policy
from linyuanzhe_frontend.contracts.hook_bus import HOOK_STAGE_PRE_CONNECTOR_REGISTRATION_REQUEST, HookBus


def main() -> int:
    req = ConnectorRegistrationRequest.build(
        display_name="L6.66 smoke MCP connector",
        kind="mcp_server",
        requested_scopes=["read_public_metadata"],
        requested_capabilities=["registry_review"],
        manifest_text="{name: l666-smoke, endpoint: redacted}",
        source_hint="l666_smoke",
    )
    bus = HookBus.default_frontend_bus()
    decision = bus.evaluate(HOOK_STAGE_PRE_CONNECTOR_REGISTRATION_REQUEST, {"payload": req.to_payload()})
    client = MockRuntimeClient()
    snapshot = client.request_connector_registration("L6.66 smoke MCP connector", "mcp_server", ["read_public_metadata"], ["registry_review"])
    public_text = json.dumps(snapshot.to_dict(), ensure_ascii=False)
    policy = connector_registry_policy()
    ok = (
        decision.ok
        and bool(snapshot.connector_registration_records)
        and snapshot.connector_registration_records[-1].no_frontend_install is True
        and snapshot.connector_registration_records[-1].no_frontend_execute is True
        and policy["market_install_disabled"] is True
        and policy["no_frontend_connector_execute"] is True
        and "endpoint: redacted" not in public_text
        and not re.search(r"(?i)mockkey_[A-Za-z0-9_\-]{12,}", public_text)
        and not re.search(r"(?i)Bearer\s+[A-Za-z0-9_\-.]{12,}", public_text)
    )
    print(json.dumps({
        "ok": ok,
        "contract": req.frontend_contract,
        "hook_verdict": decision.verdict,
        "record_status": snapshot.connector_registration_records[-1].status,
        "market_install_disabled": policy["market_install_disabled"],
        "frontend_execute_allowed": not policy["no_frontend_connector_execute"],
        "raw_secret_leaked": bool(re.search(r"(?i)mockkey_[A-Za-z0-9_\-]{12,}", public_text) or re.search(r"(?i)Bearer\s+[A-Za-z0-9_\-.]{12,}", public_text)),
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
