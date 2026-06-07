from __future__ import annotations

"""FE.01 极夜桌面驾驶舱视觉 Token。

该文件只服务前端显示，不承载执行权限，也不影响后端 Runtime。
STEP08 在 STEP07 基础上补充桌面演示级视觉层级、按钮、输入区和状态栏 token。
"""

# ---------------------------------------------------------------------------
# Color tokens
# ---------------------------------------------------------------------------
COLORS = {
    "bg_root": "#070B14",
    "bg_window": "#0B1220",
    "bg_sidebar": "#08101D",
    "bg_sidebar_2": "#0A1424",
    "bg_card": "#101A2B",
    "bg_card_2": "#121F33",
    "bg_card_3": "#16243A",
    "bg_input": "#0A1322",
    "bg_popup": "#0D1728",
    "border": "#223149",
    "border_soft": "#19263A",
    "divider": "#1A2638",
    "shadow": "#02050A",
    "text_main": "#E8EEF8",
    "text_sub": "#9AA8BA",
    "text_weak": "#66758A",
    "text_muted": "#4F5D70",
    "accent": "#3B82F6",
    "accent_hover": "#2563EB",
    "accent_soft": "#10243D",
    "accent_line": "#38BDF8",
    "selected": "#14345A",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "recover": "#8B5CF6",
    "readonly": "#64748B",
}

# ---------------------------------------------------------------------------
# Typography tokens
# ---------------------------------------------------------------------------
FONT_FAMILY_CN = "Microsoft YaHei UI"
FONT_FAMILY_LATIN = "Segoe UI"

FONTS = {
    "title": (FONT_FAMILY_CN, 18, "bold"),
    "page_title": (FONT_FAMILY_CN, 16, "bold"),
    "section_title": (FONT_FAMILY_CN, 14, "bold"),
    "card_title": (FONT_FAMILY_CN, 13, "bold"),
    "body": (FONT_FAMILY_CN, 12),
    "body_bold": (FONT_FAMILY_CN, 12, "bold"),
    "small": (FONT_FAMILY_CN, 10),
    "small_bold": (FONT_FAMILY_CN, 10, "bold"),
    "badge": (FONT_FAMILY_LATIN, 22, "bold"),
    "number": (FONT_FAMILY_LATIN, 24, "bold"),
    "mono": ("Consolas", 10),
}

# ---------------------------------------------------------------------------
# Layout tokens
# ---------------------------------------------------------------------------
DIMENS = {
    "window_w": 1440,
    "window_h": 900,
    "window_min_w": 1280,
    "window_min_h": 800,
    "topbar_h": 60,
    "sidebar_w": 172,
    "right_col_w": 348,
    "statusbar_h": 36,
    "page_pad": 20,
    "card_pad_x": 14,
    "card_pad_y": 12,
    "gap": 16,
    "gap_lg": 20,
    "button_pad_x": 14,
    "button_pad_y": 7,
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
    "danger": {"bg": COLORS["danger"], "fg": "#FFFFFF", "activebackground": "#DC2626", "activeforeground": "#FFFFFF"},
}
