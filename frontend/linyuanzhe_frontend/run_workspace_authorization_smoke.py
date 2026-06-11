from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import json
import tempfile
from pathlib import Path

from linyuanzhe_frontend.clients.mock_runtime_client import MockRuntimeClient
from linyuanzhe_frontend.contracts.hook_bus import HOOK_STAGE_PRE_WORKSPACE_AUTHORIZATION_REQUEST, HookBus
from linyuanzhe_frontend.contracts.workspace import FileAuthorizationRequest, workspace_policy


def main() -> int:
    tmp = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".txt")
    try:
        tmp.write("workspace authorization smoke\n")
        tmp.close()
        req = FileAuthorizationRequest.from_path(tmp.name, mode="read", scope="user_selected_file", purpose="smoke")
        bus = HookBus.default_frontend_bus()
        decision = bus.evaluate(HOOK_STAGE_PRE_WORKSPACE_AUTHORIZATION_REQUEST, {"payload": req.to_payload()})
        client = MockRuntimeClient()
        snapshot = client.request_file_authorization(tmp.name, "read", "user_selected_file", "smoke")
        public_text = json.dumps(snapshot.to_dict(), ensure_ascii=False)
        ok = (
            decision.ok
            and bool(snapshot.file_authorization_records)
            and snapshot.file_authorization_records[-1].raw_path_visible is False
            and str(Path(tmp.name).resolve()) not in public_text
            and workspace_policy()["runtime_authority_required"] is True
        )
        print(json.dumps({
            "ok": ok,
            "contract": req.frontend_contract,
            "hook_verdict": decision.verdict,
            "record_status": snapshot.file_authorization_records[-1].status,
            "raw_path_leaked": str(Path(tmp.name).resolve()) in public_text,
            "runtime_authority_required": workspace_policy()["runtime_authority_required"],
        }, ensure_ascii=False, indent=2))
        return 0 if ok else 1
    finally:
        try:
            Path(tmp.name).unlink(missing_ok=True)
        except Exception as exc:
            print(json.dumps({"cleanup_warning": str(exc)[:120]}, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
