from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



from pathlib import Path


def _read(rel: str) -> str:
    root = Path(__file__).resolve().parents[2]
    return (root / rel).read_text(encoding="utf-8")


def main() -> None:
    main_window = _read("frontend/linyuanzhe_frontend/ui/main_window.py")
    chat_runtime = _read("frontend/linyuanzhe_frontend/ui/main_window_chat_runtime.py")
    feature_pages = _read("frontend/linyuanzhe_frontend/ui/main_window_feature_pages.py")
    version_info = _read("frontend/linyuanzhe_frontend/version_info.py")

    checks = {
        "version_39": any(marker in version_info for marker in (
            'FE_RUNTIME_VERSION = "L6.72.39"',
            'FE_RUNTIME_VERSION = "L6.72.44"',
            'FE_RUNTIME_VERSION = "L6.72.52"',
            'FE_RUNTIME_VERSION = "L6.73.5"',
            'FE_RUNTIME_VERSION = "L6.73.8"',
        )),
        "topbar_mode_selector_removed": 'tk.Label(mode_box, text="模式"' not in main_window and 'mode_combo = ttk.Combobox(mode_box' not in main_window,
        "chat_has_single_mode_selector": chat_runtime.count('ttk.Combobox(action_col, textvariable=self.work_mode_var') == 1,
        "settings_default_mode_save_supported": '默认模式' in feature_pages and 'textvariable=self.work_mode_var' in feature_pages,
        "settings_mode_selector_single_contract": feature_pages.count('textvariable=self.work_mode_var') <= 2,
        "statusbar_theme_selector_removed": 'compact theme switch requested' not in main_window and 'text="主题"' not in main_window and 'self.theme_buttons[profile]' not in main_window,
        "settings_theme_selector_kept": 'card = Card(parent, "字体与主题"' in feature_pages and 'for idx, (key, data) in enumerate(THEME_PROFILES.items())' in feature_pages,
        "legacy_api_duplicate_form_removed": 'def _populate_api_model_settings' not in feature_pages,
        "active_model_card_kept": 'def _build_model_management_card' in feature_pages and '服务商 Provider' in feature_pages and '模型 Model' in feature_pages,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit("FAIL duplicate selection prune: " + ", ".join(failed))
    print("PASS L6.72.30-L6.73.x duplicate selection/default-mode persistence smoke")


if __name__ == "__main__":
    main()
