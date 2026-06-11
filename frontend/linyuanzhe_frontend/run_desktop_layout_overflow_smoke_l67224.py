from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



from pathlib import Path

from linyuanzhe_frontend.ui.theme import FONTS
from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION

ROOT = Path(__file__).resolve().parent
UI = ROOT / "ui"
main_text = (UI / "main_window.py").read_text(encoding="utf-8")
features = (UI / "main_window_feature_pages.py").read_text(encoding="utf-8")
widgets = (UI / "widgets.py").read_text(encoding="utf-8")

def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def _font_size(name: str) -> int:
    value = FONTS[name]
    return int(value[1])

def main() -> int:
    _assert((FE_RUNTIME_VERSION.startswith(("L6.72.", "L6.73.")) or FE_RUNTIME_VERSION.startswith("L6.73.")), "version not bumped")
    _assert("def _current_window_width" in main_text and "winfo_width()==1" in main_text, "cold-start sidebar width guard missing")
    _assert("self._adaptive_sidebar_icon_mode = self._current_window_width() < 1100" in main_text, "sidebar mode not recomputed from stable width")
    _assert("columns = 2 if current_width >= 1500 else 1" in features, "settings two-column threshold not tightened")
    _assert("_schedule_settings_page_refresh" in features, "settings debounced refresh missing")
    _assert('search.bind("<KeyRelease>", lambda _e: self.show_page("settings")' not in features, "settings search still rebuilds every keypress")
    _assert("show_subtitle = bool(kwargs.pop(\"show_subtitle\", False))" in widgets, "card subtitles are not suppressible")
    _assert("if subtitle and show_subtitle" in widgets, "card subtitles still shown by default")
    _assert("page subtitles are suppressed" in features, "page subtitle suppression missing")
    _assert("wraplength=360" in features and "wraplength=520" in features, "overflow wrap guards missing")
    _assert("_page_scroll_region_after_id" in main_text and "self.after(24, apply_region)" in main_text, "scrollregion throttle missing")
    _assert("canvas.bind(\"<Enter>\", bind_page_wheel)" in main_text, "page-local wheel binding missing")
    _assert(_font_size("page_title") > _font_size("body"), "page title is not larger than body")
    _assert(_font_size("card_title") > _font_size("body") or "body_size + 2" in (UI / "theme.py").read_text(encoding="utf-8"), "card title hierarchy not enforced")
    print("PASS desktop_layout_overflow_smoke_l67224")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
