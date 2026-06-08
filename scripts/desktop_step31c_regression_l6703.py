from __future__ import annotations

import importlib.util
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"
MAIN_WINDOW = ROOT / "frontend" / "linyuanzhe_frontend" / "ui" / "main_window.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location("linyuanzhe_bridge_l6703", BRIDGE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_provider_persistence() -> dict[str, object]:
    bridge = load_bridge()
    with tempfile.TemporaryDirectory() as td:
        cfg = Path(td) / "provider_config.json"
        old = os.environ.get("LINYUANZHE_PROVIDER_CONFIG_FILE")
        os.environ["LINYUANZHE_PROVIDER_CONFIG_FILE"] = str(cfg)
        # Environment overrides must not interfere with the persistence test.
        saved_env = {k: os.environ.pop(k, None) for k in ["LINYUANZHE_PROVIDER", "LINYUANZHE_MODEL", "LINYUANZHE_PROVIDER_BASE", "LINYUANZHE_PROVIDER_KEY"]}
        try:
            state1 = bridge.BridgeState(backend_mode="provider", timeout=30)
            result = state1.update_provider_from_payload({
                "provider": "deepseek",
                "model": "deepseek-reasoner",
                "base_url": "https://api.deepseek.com",
                "api_key": "local_secret_test_value_123456",
            })
            assert_true(cfg.exists(), "provider config file was not created")
            data = json.loads(cfg.read_text(encoding="utf-8"))
            assert_true(data.get("api_key") == "local_secret_test_value_123456", "raw key was not stored in runtime-owned config")
            assert_true(result.get("api_key_configured") is True, "api_key_configured flag missing")
            assert_true("local_secret_test" not in json.dumps(state1.provider_projection(), ensure_ascii=False), "projection leaked raw key")
            state2 = bridge.BridgeState(backend_mode="provider", timeout=30)
            proj = state2.provider_projection()
            assert_true(proj.get("api_key_configured") is True, "second bridge did not reload key")
            assert_true(proj.get("base_url_configured") is True, "second bridge did not reload base url")
            assert_true(proj.get("runtime_credential_persisted") is True, "persistence flag missing")
            return {"config_exists": cfg.exists(), "projection": {k: proj.get(k) for k in ["provider", "model", "api_key_configured", "base_url_configured", "runtime_credential_persisted"]}}
        finally:
            if old is None:
                os.environ.pop("LINYUANZHE_PROVIDER_CONFIG_FILE", None)
            else:
                os.environ["LINYUANZHE_PROVIDER_CONFIG_FILE"] = old
            for k, v in saved_env.items():
                if v is not None:
                    os.environ[k] = v


def test_chat_autoscroll_source() -> dict[str, object]:
    src = MAIN_WINDOW.read_text(encoding="utf-8")
    required = [
        "def _render_chat_messages_into",
        "body.see(\"end\")",
        "body.yview_moveto(1.0)",
        "def _render_live_chat_transcript",
        "if not self._render_live_chat_transcript(snapshot):",
        "page_key == \"settings\"",
    ]
    missing = [item for item in required if item not in src]
    assert_true(not missing, f"main_window.py missing chat/settings fixes: {missing}")
    return {"checked_patterns": len(required)}


def main() -> int:
    result = {
        "provider_persistence": test_provider_persistence(),
        "chat_autoscroll_source": test_chat_autoscroll_source(),
        "ok": True,
    }
    out = ROOT / "reports" / "desktop_step31c_regression_l6703.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
