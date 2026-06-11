from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



"""L6.73.2 Settings UX persistence and Soul scroll smoke.

This smoke is deterministic and does not launch Tk. It verifies the reported UX
class: Settings values can be edited/saved, Base URL remains visible in Settings,
Soul text has its own scrollbar/wheel handling, and UI changes remain display /
configuration only rather than tool execution.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from linyuanzhe_frontend.contracts.model_settings import sanitize_runtime_settings  # noqa: E402
from linyuanzhe_frontend.contracts.provider_settings import (  # noqa: E402
    ProviderSettingsWriteRequest,
    provider_settings_write_policy,
)
from linyuanzhe_frontend.ui.localization import host_access_scope_label, host_access_scope_value  # noqa: E402

SRC = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_base_url_visible_and_saved_contract() -> None:
    raw = {
        "provider": "deepseek",
        "model": "deepseek-v4-pro",
        "api_base_url": "https://api.deepseek.com",
        "api_key": "mockkey_test-secret",
        "host_access_scope": "全电脑 / 系统盘",
        "host_access_root": "C:/Users/example/Desktop/work",
        "persona_name": "临渊者",
        "persona_prompt": "稳定、沉着。",
    }
    settings = sanitize_runtime_settings(raw)
    require(settings["base_url_display"] == "https://api.deepseek.com", "Base URL must remain visible in sanitized Settings snapshot")
    require(settings["raw_base_url_persisted"] is True, "Base URL may persist for Settings display")
    require(settings["raw_api_key_persisted"] is False, "API Key must remain non-persistent in frontend prefs")
    request = ProviderSettingsWriteRequest.from_form(raw)
    public = request.to_public_dict()
    require(public["base_url_display"] == "https://api.deepseek.com", "Provider public dict must include base_url_display")
    require("api_key" not in public, "Provider public dict must not expose api_key")
    policy = provider_settings_write_policy()
    require(policy["write_only_fields"] == ["api_key"], "Only API Key should stay write-only")
    require(policy["frontend_may_display_base_url"] is True, "Policy must allow Settings to display Base URL")


def test_host_scope_label_mapping() -> None:
    require(host_access_scope_label("system_drive") == "全电脑 / 系统盘", "system_drive label mismatch")
    require(host_access_scope_value("全电脑 / 系统盘") == "system_drive", "Chinese host scope label must map to raw value")
    require(host_access_scope_value("自定义根目录") == "custom_root", "custom host root label must map to custom_root")


def test_settings_source_persistence_and_scroll() -> None:
    main_src = (SRC / "ui" / "main_window.py").read_text(encoding="utf-8")
    actions_src = (SRC / "ui" / "main_window_actions.py").read_text(encoding="utf-8")
    pages_src = (SRC / "ui" / "main_window_feature_pages.py").read_text(encoding="utf-8")
    sse_src = (SRC / "clients" / "sse_runtime_client.py").read_text(encoding="utf-8")
    provider_src = (SRC / "contracts" / "provider_settings.py").read_text(encoding="utf-8")
    backend_contract_src = (SRC.parents[1] / "backend" / "project" / "tiangong_agent_runtime" / "frontend_contract.py").read_text(encoding="utf-8")

    for token in ["last_base_url", "host_access_root", "model_search", "skill_search", "tool_search", "ui_preferences.v4"]:
        require(token in main_src, f"UI preference persistence missing {token}")
    require('"base_url": self.api_base_url_var.get()' in actions_src, "Runtime save payload must include visible Base URL")
    require('"host_access_root"' in actions_src, "Runtime save payload must include host_access_root")
    require("_choose_host_access_root_frontend_only" in actions_src, "Custom root chooser missing")

    require('work_mode_box = ttk.Combobox' in pages_src and '["聊天", "工作"]' in pages_src, "Settings page must allow default chat/work mode selection")
    require("Base URL 会完整保留在设置页显示" in pages_src, "Base URL visibility hint missing")
    require("host_access_scope_label(\"custom_root\")" in pages_src, "Custom root host scope option missing")
    require("保存全部设置" in pages_src and "保存外观" in pages_src and "保存数据设置" in pages_src, "Explicit save buttons missing")

    require("make_vertical_scrollbar(soul_text_shell" in pages_src, "Soul text area must have a styled scrollbar")
    require("def soul_wheel" in pages_src, "Soul text area must bind a dedicated mouse wheel handler")
    require("<MouseWheel>" in pages_src and "<Button-4>" in pages_src and "<Button-5>" in pages_src, "Soul wheel bindings missing")
    require("return \"break\"" in pages_src, "Soul wheel must not leak into page-level scroll binding")

    require("public[\"base_url_display\"] = request.base_url" in sse_src, "SSE settings submit fallback must keep Base URL visible")
    require("no_frontend_tool_execution" in provider_src, "Settings contract must preserve no direct tool execution boundary")
    require("base_url_display_field" in backend_contract_src, "Backend Settings contract must expose Base URL display field")
    require("base_url_ui_preferences_plaintext" in backend_contract_src, "Backend Settings contract must allow Base URL UI preference persistence")


def main() -> int:
    test_base_url_visible_and_saved_contract()
    test_host_scope_label_mapping()
    test_settings_source_persistence_and_scroll()
    print("L6.73.2 settings persistence / Soul scroll smoke PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
