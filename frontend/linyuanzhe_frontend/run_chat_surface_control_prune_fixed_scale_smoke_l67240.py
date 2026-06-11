from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



from pathlib import Path

from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION
from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    root = Path(__file__).resolve().parent
    chat = (root / "ui" / "main_window_chat_runtime.py").read_text(encoding="utf-8")
    main = (root / "ui" / "main_window.py").read_text(encoding="utf-8")
    feature = (root / "ui" / "main_window_feature_pages.py").read_text(encoding="utf-8")
    theme = (root / "ui" / "theme.py").read_text(encoding="utf-8")

    require((FE_RUNTIME_VERSION.startswith(("L6.72.", "L6.73.")) or FE_RUNTIME_VERSION.startswith("L6.73.")), "version must be L6.72.41+ compatible")
    require('body.bind("<<Copy>>", self._copy_selected_chat_text_event' in chat, "selected chat copy binding missing")
    require('def _get_selected_chat_text' in chat, "selected chat copy helper missing")
    require('text="新对话"' in chat or '("新对话",' in chat, "bottom new chat button missing")
    require(('text="引导"' in chat or '("引导",' in chat) and ('text="中断"' in chat or '("中断",' in chat), "guide/interrupt buttons missing")
    require('text="清屏"' not in chat and 'text="复位"' not in chat and 'text="执行"' not in chat, "old bottom control buttons still present")
    require('for icon in ("🙂", "👍", "🔥", "✅")' not in chat, "emoji quick buttons still present")
    require('当前页唯一模式选择' not in chat, "work-mode explanation should be removed")
    require('mode_combo.grid(row=0, column=0, sticky="ew"' in chat, "work mode selector not moved to input action column")
    require('actions = [("新会话"' not in main, "topbar new conversation button should be removed")
    require('_build_config_file_card' not in feature, "config file card should be removed from frontend")
    require('DIMENS["card_pad_x"] = _clamp_int(round(12 * scale)' not in theme, "settings scale should not mutate layout dimensions")
    require('self.show_page(self.current_page)' in main and '_rebuild_shell_after_theme()' not in main.split('def _apply_typography_selection', 1)[1].split('def _current_window_width', 1)[0], "typography must not rebuild full shell")

    s = RuntimeSnapshot()
    s.append_user_message("复制测试", timestamp="")
    require(s.chat_messages[-2].time.count(":") >= 2, "user message timestamp should use clock time")

    print("PASS L6.72.41-L6.72.43 chat surface control prune + fixed scale smoke")


if __name__ == "__main__":
    main()
