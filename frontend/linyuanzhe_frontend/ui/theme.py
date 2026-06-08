from __future__ import annotations

"""FE.01 桌面端视觉 Token。

该文件只服务前端显示，不承载执行权限，也不影响后端 Runtime。
L6.71.7 将默认视觉从蓝黑监控感调整为中性工作台：降低装饰色、提高文字对比、
保留永夜/极昼/墨绿三套外观，并继续使用系统字体。
"""

# ---------------------------------------------------------------------------
# Color tokens
# ---------------------------------------------------------------------------
COLORS = {
    "bg_root": "#0C0E11",
    "bg_window": "#101215",
    "bg_sidebar": "#0F1114",
    "bg_sidebar_2": "#15191E",
    "bg_card": "#15191E",
    "bg_card_2": "#1A1F25",
    "bg_card_3": "#20262D",
    "bg_input": "#0F1216",
    "bg_popup": "#15191E",
    "border": "#29313A",
    "border_soft": "#20272F",
    "divider": "#222A33",
    "shadow": "#050607",
    "text_main": "#ECEFF3",
    "text_sub": "#AAB3BE",
    "text_weak": "#7F8A96",
    "text_muted": "#5F6A75",
    "accent": "#14B8A6",
    "accent_hover": "#0F9F91",
    "accent_soft": "#102522",
    "accent_line": "#2DD4BF",
    "selected": "#192223",
    "success": "#22C55E",
    "warning": "#D97706",
    "danger": "#DC2626",
    "recover": "#8B5CF6",
    "readonly": "#64748B",
}

THEME_PROFILES = {
    "midnight": {
        "label": "永夜",
        "bg_root": "#0C0E11",
        "bg_window": "#101215",
        "bg_sidebar": "#0F1114",
        "bg_sidebar_2": "#15191E",
        "bg_card": "#15191E",
        "bg_card_2": "#1A1F25",
        "bg_card_3": "#20262D",
        "bg_input": "#0F1216",
        "bg_popup": "#15191E",
        "border": "#29313A",
        "border_soft": "#20272F",
        "divider": "#222A33",
        "shadow": "#050607",
        "text_main": "#ECEFF3",
        "text_sub": "#AAB3BE",
        "text_weak": "#7F8A96",
        "text_muted": "#5F6A75",
        "accent": "#14B8A6",
        "accent_hover": "#0F9F91",
        "accent_soft": "#102522",
        "accent_line": "#2DD4BF",
        "selected": "#192223",
    },
    "warm_gray": {
        "label": "极昼",
        "bg_root": "#F6F7F5",
        "bg_window": "#FFFFFF",
        "bg_sidebar": "#F1F2EF",
        "bg_sidebar_2": "#FFFFFF",
        "bg_card": "#FFFFFF",
        "bg_card_2": "#F3F5F4",
        "bg_card_3": "#ECEFED",
        "bg_input": "#FAFBFA",
        "bg_popup": "#FFFFFF",
        "border": "#D5DAD6",
        "border_soft": "#E2E6E2",
        "divider": "#DDE2DE",
        "shadow": "#D7DCD8",
        "text_main": "#1F2428",
        "text_sub": "#55606A",
        "text_weak": "#7A858E",
        "text_muted": "#9AA3AA",
        "accent": "#0F766E",
        "accent_hover": "#0B5F59",
        "accent_soft": "#DDF4F0",
        "accent_line": "#0F766E",
        "selected": "#DFF3EE",
    },
    "ink_green": {
        "label": "墨绿",
        "bg_root": "#07110F",
        "bg_window": "#0A1714",
        "bg_sidebar": "#081511",
        "bg_sidebar_2": "#0D211B",
        "bg_card": "#10231E",
        "bg_card_2": "#153027",
        "bg_card_3": "#1B3B31",
        "bg_input": "#0B1E19",
        "bg_popup": "#10231E",
        "border": "#244A3F",
        "border_soft": "#1C3A32",
        "divider": "#1E3D35",
        "shadow": "#020706",
        "text_main": "#E8F4F0",
        "text_sub": "#A9C4BA",
        "text_weak": "#78958C",
        "text_muted": "#566F67",
        "accent": "#10B981",
        "accent_hover": "#059669",
        "accent_soft": "#0D352B",
        "accent_line": "#34D399",
        "selected": "#17483A",
    },
}


def apply_theme_profile(profile: str) -> str:
    key = profile if profile in THEME_PROFILES else "midnight"
    COLORS.update(THEME_PROFILES[key])
    BUTTON_STYLES["primary"].update({"bg": COLORS["accent"], "activebackground": COLORS["accent_hover"]})
    BUTTON_STYLES["secondary"].update({"bg": COLORS["bg_card_2"], "fg": COLORS["text_main"], "activebackground": COLORS["selected"], "activeforeground": COLORS["text_main"]})
    BUTTON_STYLES["ghost"].update({"bg": COLORS["bg_window"], "fg": COLORS["text_sub"], "activebackground": COLORS["bg_card_2"], "activeforeground": COLORS["text_main"]})
    return key

# ---------------------------------------------------------------------------
# Typography tokens
# ---------------------------------------------------------------------------
# TkDefaultFont follows the platform default font on Windows/macOS/Linux.  It
# avoids shipping font files and keeps the desktop shell native-looking.
FONT_FAMILY_CN = "TkDefaultFont"
FONT_FAMILY_LATIN = "TkDefaultFont"
FONT_FAMILY_MONO = "TkFixedFont"

FONTS = {
    "title": (FONT_FAMILY_CN, 16, "bold"),
    "page_title": (FONT_FAMILY_CN, 15, "bold"),
    "section_title": (FONT_FAMILY_CN, 13, "bold"),
    "card_title": (FONT_FAMILY_CN, 12, "bold"),
    "body": (FONT_FAMILY_CN, 11),
    "body_bold": (FONT_FAMILY_CN, 11, "bold"),
    "small": (FONT_FAMILY_CN, 10),
    "small_bold": (FONT_FAMILY_CN, 10, "bold"),
    "badge": (FONT_FAMILY_LATIN, 18, "bold"),
    "number": (FONT_FAMILY_LATIN, 20, "bold"),
    "mono": (FONT_FAMILY_MONO, 10),
}

# ---------------------------------------------------------------------------
# Layout tokens
# ---------------------------------------------------------------------------
DIMENS = {
    "window_w": 1440,
    "window_h": 900,
    "window_min_w": 1180,
    "window_min_h": 760,
    "topbar_h": 46,
    "sidebar_w": 116,
    "right_col_w": 332,
    "statusbar_h": 32,
    "page_pad": 12,
    "card_pad_x": 12,
    "card_pad_y": 10,
    "gap": 12,
    "gap_lg": 16,
    "button_pad_x": 12,
    "button_pad_y": 6,
}

STATUS_COLORS = {
    "RUNNING": COLORS["accent"],
    "READY": COLORS["success"],
    "COMPLETED": COLORS["success"],
    "DISCONNECTED": COLORS["warning"],
    "FAILED": COLORS["danger"],
    "BLOCKED": COLORS["danger"],
    "PENDING": COLORS["warning"],
    "succeeded": COLORS["success"],
    "running": COLORS["accent"],
    "queued": COLORS["readonly"],
    "blocked": COLORS["danger"],
    "failed": COLORS["danger"],
    "confirmation_required": COLORS["warning"],
    "recovered": COLORS["recover"],
    "timeout": COLORS["warning"],
    "warning": COLORS["warning"],
    "ok": COLORS["success"],
}

BUTTON_STYLES = {
    "primary": {"bg": COLORS["accent"], "fg": "#FFFFFF", "activebackground": COLORS["accent_hover"], "activeforeground": "#FFFFFF"},
    "secondary": {"bg": COLORS["bg_card_2"], "fg": COLORS["text_main"], "activebackground": COLORS["selected"], "activeforeground": COLORS["text_main"]},
    "ghost": {"bg": COLORS["bg_window"], "fg": COLORS["text_sub"], "activebackground": COLORS["bg_card_2"], "activeforeground": COLORS["text_main"]},
    "success": {"bg": COLORS["success"], "fg": "#FFFFFF", "activebackground": "#16A34A", "activeforeground": "#FFFFFF"},
    "danger": {"bg": COLORS["danger"], "fg": "#FFFFFF", "activebackground": "#B91C1C", "activeforeground": "#FFFFFF"},
}
