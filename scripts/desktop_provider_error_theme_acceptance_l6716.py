from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

from linyuanzhe_frontend.clients.mock_runtime_client import MockRuntimeClient
from linyuanzhe_frontend.contracts.provider_settings import provider_error_user_hint, provider_readiness_from_public_projection
from linyuanzhe_frontend.ui.main_window import LinyuanzheDesktopApp


def main() -> int:
    report_dir = ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    gateway = provider_readiness_from_public_projection({
        "api_key_configured": True,
        "base_url_configured": True,
        "effective_backend_mode": "provider",
        "requested_backend_mode": "auto",
        "provider_config_state": "error",
        "last_provider_check_state": "failed",
        "last_provider_error_code": "gateway_unreachable",
        "last_provider_error_message": "connection refused <redacted>",
    }).to_dict()
    auth = provider_readiness_from_public_projection({
        "api_key_configured": True,
        "base_url_configured": True,
        "effective_backend_mode": "provider",
        "requested_backend_mode": "auto",
        "provider_config_state": "error",
        "last_provider_check_state": "failed",
        "last_provider_error_code": "auth_failed",
        "last_provider_error_message": "401 unauthorized <redacted>",
    }).to_dict()

    app = LinyuanzheDesktopApp(MockRuntimeClient())
    try:
        app.show_page("chat")
        app.update_idletasks()
        theme_buttons_initial = set(getattr(app, "theme_buttons", {}).keys())
        app._set_theme_profile("warm_gray")
        app.update_idletasks()
        switched_to_day = app.theme_profile_var.get() == "warm_gray"
        # Rebuild happens during theme switch. Check buttons again after rebuild.
        theme_buttons_after = set(getattr(app, "theme_buttons", {}).keys())
        app._set_theme_profile("midnight")
        app.update_idletasks()
        switched_to_night = app.theme_profile_var.get() == "midnight"
        app.show_page("settings")
        app.update_idletasks()
        checks = {
            "gateway_error_classified": gateway.get("readiness") == "error" and gateway.get("config_error_code") == "gateway_unreachable" and "Tailscale" in gateway.get("primary_action", ""),
            "auth_error_classified": auth.get("readiness") == "error" and auth.get("config_error_code") == "auth_failed" and "API Key" in auth.get("label", ""),
            "provider_error_hint_has_next_action": "复测" in provider_error_user_hint("gateway_unreachable")[1],
            "bottom_theme_buttons_present_initially": {"midnight", "warm_gray"}.issubset(theme_buttons_initial),
            "bottom_theme_buttons_survive_rebuild": {"midnight", "warm_gray"}.issubset(theme_buttons_after),
            "bottom_theme_can_switch_to_extreme_day": switched_to_day,
            "bottom_theme_can_switch_back_to_extreme_night": switched_to_night,
            "settings_hint_mentions_bottom_switch": "底框" in Path(ROOT / "frontend" / "linyuanzhe_frontend" / "ui" / "main_window.py").read_text(encoding="utf-8"),
            "no_raw_secret_in_error_projection": "mockkey_" not in json.dumps({"gateway": gateway, "auth": auth}, ensure_ascii=False).lower(),
        }
        payload = {
            "schema": "tiangong.fe01.step31p.provider_error_theme_acceptance.v1",
            "ok": all(checks.values()),
            "checks": checks,
            "readiness_samples": {"gateway_unreachable": gateway, "auth_failed": auth},
            "note": "Validates Provider error-state classification and bottom-frame 永夜/极昼 theme quick switch. It does not call Provider SDKs, tools, memory, audit, or official Runtime RC.",
        }
        (report_dir / "step31p_provider_error_theme_acceptance.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return 0 if payload["ok"] else 1
    finally:
        app.destroy()


if __name__ == "__main__":
    raise SystemExit(main())
