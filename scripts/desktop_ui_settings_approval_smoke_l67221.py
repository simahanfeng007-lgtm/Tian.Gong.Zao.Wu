from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "theme": ROOT / "frontend" / "linyuanzhe_frontend" / "ui" / "theme.py",
    "settings": ROOT / "frontend" / "linyuanzhe_frontend" / "ui" / "main_window_feature_pages.py",
    "chat": ROOT / "frontend" / "linyuanzhe_frontend" / "ui" / "main_window_chat_runtime.py",
    "actions": ROOT / "frontend" / "linyuanzhe_frontend" / "ui" / "main_window_actions.py",
    "main": ROOT / "frontend" / "linyuanzhe_frontend" / "ui" / "main_window.py",
    "widgets": ROOT / "frontend" / "linyuanzhe_frontend" / "ui" / "widgets.py",
}

checks: dict[str, bool] = {}
texts = {name: path.read_text(encoding="utf-8") for name, path in FILES.items()}

checks["five_theme_profiles"] = all(key in texts["theme"] for key in ["midnight", "warm_gray", "ink_green", "warm_gold", "fog_blue"])
checks["font_catalog"] = all(key in texts["theme"] for key in ["source_han_sans", "lxgw_wenkai", "sarasa_gothic", "fira_code", "cascadia_code", "jetbrains_mono"])
checks["typography_runtime_apply"] = "apply_typography_preferences" in texts["main"] and "_apply_typography_selection" in texts["main"]
checks["settings_model_soul_split"] = "_build_model_management_card" in texts["settings"] and "_build_soul_settings_card" in texts["settings"]
checks["skill_tool_tooltip"] = "Tooltip(" in texts["settings"] and "_collect_skill_items" in texts["settings"] and "_collect_tool_items" in texts["settings"]
checks["runtime_config_collapsible"] = "_toggle_runtime_status_card" in texts["actions"] and "_toggle_config_file_card" in texts["actions"]
checks["permission_modal"] = "_show_permission_approval_modal" in texts["chat"] and "批准一次" in texts["chat"] and "本次会话始终批准" in texts["chat"] and "60000" in texts["chat"]
checks["chat_context_menu"] = "_show_message_context_menu" in texts["chat"] and "复制最后代码块" in texts["chat"]
checks["new_message_scroll_guard"] = "_show_new_message_button" in texts["chat"] and "_chat_should_auto_scroll" in texts["chat"]
checks["shortcut_bindings"] = all(key in texts["main"] for key in ["<Control-l>", "<Control-n>", "<Control-comma>", "<Escape>", "<Control-Shift-C>"])
checks["frontend_no_runtime_core_touch"] = not any((ROOT / path).exists() and "L6.72.21" in (ROOT / path).read_text(encoding="utf-8", errors="ignore") for path in ["backend/project/tiangong_kernel.py"])

ok = all(checks.values())
print(json.dumps({"ok": ok, "contract": "tiangong.l6_72_21.desktop_ui_settings_approval.v1", "checks": checks}, ensure_ascii=False, indent=2))
raise SystemExit(0 if ok else 1)
