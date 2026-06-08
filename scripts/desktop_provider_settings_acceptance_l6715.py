from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

from linyuanzhe_frontend.clients.mock_runtime_client import MockRuntimeClient
from linyuanzhe_frontend.contracts.provider_settings import provider_readiness_from_public_projection
from linyuanzhe_frontend.ui.main_window import LinyuanzheDesktopApp


def main() -> int:
    report_dir = ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    missing = provider_readiness_from_public_projection({}).to_dict()
    ready = provider_readiness_from_public_projection({
        "api_key_configured": True,
        "base_url_configured": True,
        "effective_backend_mode": "provider",
        "requested_backend_mode": "auto",
        "provider_config_state": "ready",
    }).to_dict()
    forced = provider_readiness_from_public_projection({
        "api_key_configured": True,
        "base_url_configured": True,
        "effective_backend_mode": "mock",
        "requested_backend_mode": "mock",
        "provider_config_state": "forced_mock",
    }).to_dict()

    app = LinyuanzheDesktopApp(MockRuntimeClient())
    try:
        app.show_page("settings")
        app.update_idletasks()
        app.api_provider_var.set("openai_compatible")
        app.main_model_var.set("deepseek-v4-pro")
        app.api_base_url_var.set("https://example.invalid/v1")
        app.api_key_var.set("secret-value-that-must-not-enter-template")
        app._copy_provider_config_template_frontend_only()
        try:
            template_text = app.clipboard_get()
        except Exception:
            template_text = ""
        app._save_runtime_settings_frontend_only()
        status_after_save = app.settings_status_var.get()
        checks = {
            "missing_projection_detects_both_fields": missing.get("readiness") == "missing_credentials" and set(missing.get("missing_fields", [])) == {"api_key", "base_url"},
            "ready_projection_detected": ready.get("can_use_real_model") is True and ready.get("readiness") == "ready",
            "forced_mock_projection_detected": forced.get("readiness") == "forced_mock" and forced.get("mock_mode") is True,
            "template_contains_placeholders": "<write-only-api-key>" in template_text and "<write-only-base-url>" in template_text,
            "template_omits_raw_key": "secret-value-that-must-not-enter-template" not in template_text,
            "save_clears_raw_api_key": app.api_key_var.get() == "",
            "save_clears_raw_base_url": app.api_base_url_var.get() == "",
            "mock_save_does_not_claim_provider_call": "未调用 Provider" in status_after_save,
            "home_mode_mentions_provider_state": "provider" in app._home_mode_label(app.snapshot).lower() or "mock" in app._home_mode_label(app.snapshot).lower(),
        }
        payload = {
            "schema": "tiangong.fe01.step31o.provider_settings_acceptance.v1",
            "ok": all(checks.values()),
            "checks": checks,
            "readiness_samples": {"missing": missing, "ready": ready, "forced": forced},
            "note": "Provider UX acceptance validates digest-only readiness, template safety, raw input clearing, and Mock boundary. It does not call Provider SDKs, tools, memory, audit, or official Runtime RC.",
        }
        (report_dir / "step31o_provider_settings_acceptance.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return 0 if payload["ok"] else 1
    finally:
        app.destroy()


if __name__ == "__main__":
    raise SystemExit(main())
