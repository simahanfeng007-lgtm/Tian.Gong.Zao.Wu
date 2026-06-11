from __future__ import annotations

"""FE.01 / L6.72.24 桌面端视觉 Token。

只服务前端显示与本地偏好，不承载执行权限，不影响 Runtime、PromptCore、tiangong_kernel。
字体不随包分发，只声明候选字体并交给 Tk/系统 fallback。
"""

COLORS = {
    "bg_root": "#12161C",
    "bg_window": "#171C23",
    "bg_sidebar": "#141922",
    "bg_sidebar_2": "#1B222B",
    "bg_card": "#1B222B",
    "bg_card_2": "#222B36",
    "bg_card_3": "#2A3442",
    "bg_input": "#171D25",
    "bg_popup": "#1B222B",
    "border": "#33404E",
    "border_soft": "#293442",
    "divider": "#2C3745",
    "shadow": "#090C10",
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
        "label": "永夜", "bg_root": "#12161C", "bg_window": "#171C23", "bg_sidebar": "#141922", "bg_sidebar_2": "#1B222B",
        "bg_card": "#1B222B", "bg_card_2": "#222B36", "bg_card_3": "#2A3442", "bg_input": "#171D25", "bg_popup": "#1B222B",
        "border": "#33404E", "border_soft": "#293442", "divider": "#2C3745", "shadow": "#090C10", "text_main": "#ECEFF3",
        "text_sub": "#AAB3BE", "text_weak": "#7F8A96", "text_muted": "#5F6A75", "accent": "#14B8A6", "accent_hover": "#0F9F91",
        "accent_soft": "#102522", "accent_line": "#2DD4BF", "selected": "#192223",
    },
    "warm_gray": {
        "label": "极昼", "bg_root": "#F6F7F5", "bg_window": "#FFFFFF", "bg_sidebar": "#F1F2EF", "bg_sidebar_2": "#FFFFFF",
        "bg_card": "#FFFFFF", "bg_card_2": "#F3F5F4", "bg_card_3": "#ECEFED", "bg_input": "#FAFBFA", "bg_popup": "#FFFFFF",
        "border": "#D5DAD6", "border_soft": "#E2E6E2", "divider": "#DDE2DE", "shadow": "#D7DCD8", "text_main": "#1F2428",
        "text_sub": "#55606A", "text_weak": "#7A858E", "text_muted": "#9AA3AA", "accent": "#0F766E", "accent_hover": "#0B5F59",
        "accent_soft": "#DDF4F0", "accent_line": "#0F766E", "selected": "#DFF3EE",
    },
    "ink_green": {
        "label": "墨绿", "bg_root": "#07110F", "bg_window": "#0A1714", "bg_sidebar": "#081511", "bg_sidebar_2": "#0D211B",
        "bg_card": "#10231E", "bg_card_2": "#153027", "bg_card_3": "#1B3B31", "bg_input": "#0B1E19", "bg_popup": "#10231E",
        "border": "#244A3F", "border_soft": "#1C3A32", "divider": "#1E3D35", "shadow": "#020706", "text_main": "#E8F4F0",
        "text_sub": "#A9C4BA", "text_weak": "#78958C", "text_muted": "#566F67", "accent": "#10B981", "accent_hover": "#059669",
        "accent_soft": "#0D352B", "accent_line": "#34D399", "selected": "#17483A",
    },
    "warm_gold": {
        "label": "暖金", "bg_root": "#17120A", "bg_window": "#1F180D", "bg_sidebar": "#1A1308", "bg_sidebar_2": "#251B0D",
        "bg_card": "#261B0E", "bg_card_2": "#332412", "bg_card_3": "#403018", "bg_input": "#1E160B", "bg_popup": "#261B0E",
        "border": "#604418", "border_soft": "#493515", "divider": "#473414", "shadow": "#070501", "text_main": "#FFF7E8",
        "text_sub": "#D9C7A2", "text_weak": "#A89166", "text_muted": "#7F6C48", "accent": "#D97706", "accent_hover": "#B45309",
        "accent_soft": "#3A2508", "accent_line": "#F59E0B", "selected": "#3B2A10",
    },
    "fog_blue": {
        "label": "雾蓝", "bg_root": "#101820", "bg_window": "#16212B", "bg_sidebar": "#121C25", "bg_sidebar_2": "#1B2834",
        "bg_card": "#1B2834", "bg_card_2": "#243442", "bg_card_3": "#2E4150", "bg_input": "#17232E", "bg_popup": "#1B2834",
        "border": "#3B5363", "border_soft": "#304554", "divider": "#344A59", "shadow": "#060A0D", "text_main": "#EDF5FA",
        "text_sub": "#B7C8D5", "text_weak": "#8397A5", "text_muted": "#627581", "accent": "#38BDF8", "accent_hover": "#0284C7",
        "accent_soft": "#102B3A", "accent_line": "#7DD3FC", "selected": "#183342",
    },
}

UI_FONT_FAMILIES = {
    "system": "TkDefaultFont",
    "source_han_sans": "Source Han Sans SC",
    "lxgw_wenkai": "LXGW WenKai",
    "sarasa_gothic": "Sarasa Gothic SC",
}
CODE_FONT_FAMILIES = {
    "fira_code": "Fira Code",
    "cascadia_code": "Cascadia Code",
    "jetbrains_mono": "JetBrains Mono",
    "tk_fixed": "TkFixedFont",
}
TYPOGRAPHY_DEFAULTS = {
    "ui_font_family": "system",
    "chat_font_size": 15,
    "settings_scale": 1.0,
    "line_height": 1.8,
    "code_font_family": "cascadia_code",
    "code_ligatures": False,
}

FONT_FAMILY_CN = UI_FONT_FAMILIES["system"]
FONT_FAMILY_LATIN = UI_FONT_FAMILIES["system"]
FONT_FAMILY_MONO = CODE_FONT_FAMILIES["tk_fixed"]

FONTS = {
    "title": (FONT_FAMILY_CN, 17, "bold"),
    "page_title": (FONT_FAMILY_CN, 17, "bold"),
    "section_title": (FONT_FAMILY_CN, 14, "bold"),
    "card_title": (FONT_FAMILY_CN, 13, "bold"),
    "body": (FONT_FAMILY_CN, 11),
    "body_bold": (FONT_FAMILY_CN, 11, "bold"),
    "small": (FONT_FAMILY_CN, 10),
    "small_bold": (FONT_FAMILY_CN, 10, "bold"),
    "badge": (FONT_FAMILY_LATIN, 18, "bold"),
    "number": (FONT_FAMILY_LATIN, 20, "bold"),
    "mono": (FONT_FAMILY_MONO, 10),
    "mono_small": (FONT_FAMILY_MONO, 9),
}

DIMENS = {
    "window_w": 1280,
    "window_h": 800,
    "window_min_w": 1040,
    "window_min_h": 650,
    "content_min_w": 640,
    "chat_input_min_h": 116,
    "topbar_h": 38,
    "sidebar_w": 132,
    "sidebar_icon_w": 56,
    "right_col_w": 332,
    "statusbar_h": 24,
    "page_pad": 10,
    "card_pad_x": 12,
    "card_pad_y": 10,
    "gap": 12,
    "gap_lg": 16,
    "button_pad_x": 12,
    "button_pad_y": 6,
    "transition_ms": 200,
}

STATUS_COLORS = {
    "RUNNING": COLORS["accent"], "READY": COLORS["success"], "COMPLETED": COLORS["success"], "DISCONNECTED": COLORS["warning"],
    "FAILED": COLORS["danger"], "BLOCKED": COLORS["danger"], "PENDING": COLORS["warning"], "succeeded": COLORS["success"],
    "running": COLORS["accent"], "queued": COLORS["readonly"], "blocked": COLORS["danger"], "failed": COLORS["danger"],
    "confirmation_required": COLORS["warning"], "recovered": COLORS["recover"], "timeout": COLORS["warning"], "warning": COLORS["warning"],
    "ok": COLORS["success"], "low": COLORS["success"], "medium": COLORS["warning"], "high": COLORS["danger"],
}

BUTTON_STYLES = {
    "primary": {"bg": COLORS["accent"], "fg": "#FFFFFF", "activebackground": COLORS["accent_hover"], "activeforeground": "#FFFFFF"},
    "secondary": {"bg": COLORS["bg_card_2"], "fg": COLORS["text_main"], "activebackground": COLORS["selected"], "activeforeground": COLORS["text_main"]},
    "ghost": {"bg": COLORS["bg_window"], "fg": COLORS["text_sub"], "activebackground": COLORS["bg_card_2"], "activeforeground": COLORS["text_main"]},
    "success": {"bg": COLORS["success"], "fg": "#FFFFFF", "activebackground": "#16A34A", "activeforeground": "#FFFFFF"},
    "danger": {"bg": COLORS["danger"], "fg": "#FFFFFF", "activebackground": "#B91C1C", "activeforeground": "#FFFFFF"},
}


def _clamp_int(value: object, default: int, low: int, high: int) -> int:
    try:
        number = int(value)  # type: ignore[arg-type]
    except Exception:
        number = default
    return max(low, min(high, number))


def _clamp_float(value: object, default: float, low: float, high: float) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except Exception:
        number = default
    return max(low, min(high, number))


def apply_theme_profile(profile: str) -> str:
    key = profile if profile in THEME_PROFILES else "midnight"
    COLORS.update(THEME_PROFILES[key])
    BUTTON_STYLES["primary"].update({"bg": COLORS["accent"], "activebackground": COLORS["accent_hover"]})
    BUTTON_STYLES["secondary"].update({"bg": COLORS["bg_card_2"], "fg": COLORS["text_main"], "activebackground": COLORS["selected"], "activeforeground": COLORS["text_main"]})
    BUTTON_STYLES["ghost"].update({"bg": COLORS["bg_window"], "fg": COLORS["text_sub"], "activebackground": COLORS["bg_card_2"], "activeforeground": COLORS["text_main"]})
    return key


def apply_typography_preferences(
    *,
    ui_font_family: str = "system",
    chat_font_size: int | str = 14,
    settings_scale: float | str = 1.0,
    line_height: float | str = 1.6,
    code_font_family: str = "cascadia_code",
    code_ligatures: bool | str = False,
) -> dict[str, object]:
    ui_key = ui_font_family if ui_font_family in UI_FONT_FAMILIES else "system"
    code_key = code_font_family if code_font_family in CODE_FONT_FAMILIES else "cascadia_code"
    chat_size = _clamp_int(chat_font_size, 15, 12, 18)
    scale = _clamp_float(settings_scale, 1.0, 0.85, 1.25)
    leading = _clamp_float(line_height, 1.8, 1.4, 2.0)
    ui_family = UI_FONT_FAMILIES[ui_key]
    mono_family = CODE_FONT_FAMILIES[code_key]
    body_size = _clamp_int(round(chat_size * 0.86 * scale), 12, 10, 18)
    small_size = max(9, body_size - 1)
    FONTS.update({
        "title": (ui_family, max(16, body_size + 6), "bold"),
        "page_title": (ui_family, max(16, body_size + 5), "bold"),
        "section_title": (ui_family, max(13, body_size + 3), "bold"),
        "card_title": (ui_family, max(12, body_size + 2), "bold"),
        "body": (ui_family, body_size),
        "body_bold": (ui_family, body_size, "bold"),
        "chat_body": (ui_family, chat_size),
        "chat_body_bold": (ui_family, chat_size, "bold"),
        "small": (ui_family, small_size),
        "small_bold": (ui_family, small_size, "bold"),
        "badge": (ui_family, max(16, body_size + 7), "bold"),
        "number": (ui_family, max(18, body_size + 8), "bold"),
        "mono": (mono_family, max(10, chat_size - 1)),
        "mono_small": (mono_family, max(9, chat_size - 2)),
    })
    # L6.72.40: settings scale is visual scale only.  Do not mutate layout
    # dimensions here; changing DIMENS caused sidebar/card reflow and visible
    # flicker.  Grid proportions remain fixed while fonts scale.
    return {
        "ui_font_family": ui_key,
        "chat_font_size": chat_size,
        "settings_scale": scale,
        "line_height": leading,
        "code_font_family": code_key,
        "code_ligatures": bool(code_ligatures),
    }
