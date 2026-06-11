from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from .theme import BUTTON_STYLES, COLORS, DIMENS, FONTS, STATUS_COLORS
from .localization import ui_text


# ---------------------------------------------------------------------------
# Global ttk style
# ---------------------------------------------------------------------------
def configure_ttk_style(root: tk.Tk) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        # Some headless/minimal Tk builds do not ship the clam theme.
        style.theme_use(style.theme_use())
    style.configure(
        "LZ.Horizontal.TProgressbar",
        troughcolor=COLORS["bg_window"],
        background=COLORS["accent"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["accent"],
        darkcolor=COLORS["accent"],
        thickness=10,
    )
    _configure_scrollbar_style(style, "LZ.Vertical.TScrollbar", trough=COLORS["bg_root"], thumb=COLORS["bg_card_3"])
    _configure_scrollbar_style(style, "LZ.Chat.Vertical.TScrollbar", trough=COLORS["bg_card"], thumb=COLORS["bg_card_3"])
    _configure_scrollbar_style(style, "LZ.Sidebar.Vertical.TScrollbar", trough=COLORS["bg_card_2"], thumb=COLORS["bg_card_3"])


def _configure_scrollbar_style(style: ttk.Style, name: str, *, trough: str, thumb: str) -> None:
    """统一美化侧边/会话滑条，避免暗色主题下原生滑条刺眼。"""
    style.configure(
        name,
        gripcount=0,
        background=thumb,
        darkcolor=thumb,
        lightcolor=thumb,
        troughcolor=trough,
        bordercolor=COLORS["border_soft"],
        arrowcolor=COLORS["text_weak"],
        relief="flat",
        width=12,
        arrowsize=12,
    )
    style.map(
        name,
        background=[("pressed", COLORS["accent_hover"]), ("active", COLORS["accent"])],
        arrowcolor=[("pressed", "#FFFFFF"), ("active", "#FFFFFF")],
    )


def make_vertical_scrollbar(master: tk.Misc, command, *, variant: str = "page") -> ttk.Scrollbar:
    """创建统一样式的竖向滑条。

    前端只替换显示控件，不改变滚动数据结构、不参与 Runtime 语义判断。
    """
    style_name = {
        "chat": "LZ.Chat.Vertical.TScrollbar",
        "sidebar": "LZ.Sidebar.Vertical.TScrollbar",
    }.get(str(variant or "page"), "LZ.Vertical.TScrollbar")
    return ttk.Scrollbar(master, orient="vertical", command=command, style=style_name)


# ---------------------------------------------------------------------------
# Primitive components
# ---------------------------------------------------------------------------
class Card(tk.Frame):
    """桌面卡片组件。

    tkinter 没有原生圆角和 CSS 阴影；FE.01 使用统一背景、细描边、标题层级和留白，
    保持未来迁移到自绘 Canvas / ttk theme 时的组件边界稳定。
    """

    def __init__(self, master: tk.Misc, title: str = "", subtitle: str = "", **kwargs) -> None:
        # L6.72.24: subtitles are intentionally suppressed by default.
        # The desktop shell was visually noisy because every card/page title
        # carried a second explanatory line. Explanatory copy now belongs in the
        # card body as explicit hints, not directly under titles.
        show_subtitle = bool(kwargs.pop("show_subtitle", False))
        super().__init__(
            master,
            bg=COLORS["bg_card"],
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["border"],
            highlightthickness=1,
            **kwargs,
        )
        self.columnconfigure(0, weight=1)
        if title:
            header = tk.Frame(self, bg=COLORS["bg_card"])
            header.grid(row=0, column=0, sticky="ew", padx=DIMENS["card_pad_x"], pady=(DIMENS["card_pad_y"], 4))
            header.grid_columnconfigure(0, weight=1)
            tk.Label(
                header,
                text=ui_text(title),
                bg=COLORS["bg_card"],
                fg=COLORS["text_main"],
                font=FONTS["card_title"],
                anchor="w",
                justify="left",
                wraplength=620,
            ).grid(row=0, column=0, sticky="ew")
            if subtitle and show_subtitle:
                tk.Label(header, text=ui_text(subtitle), bg=COLORS["bg_card"], fg=COLORS["text_weak"], font=FONTS["small"], wraplength=620, justify="left").grid(row=1, column=0, sticky="ew", pady=(3, 0))


class Divider(tk.Frame):
    def __init__(self, master: tk.Misc, bg: Optional[str] = None) -> None:
        super().__init__(master, bg=bg or COLORS["divider"], height=1)
        self.grid_propagate(False)


class StatusDot(tk.Label):
    def __init__(self, master: tk.Misc, status: str = "running", size: int = 9) -> None:
        color = STATUS_COLORS.get(status, COLORS["success"])
        super().__init__(master, text="●", bg=master.cget("bg") if hasattr(master, "cget") else COLORS["bg_card"], fg=color, font=("Segoe UI", size, "bold"))


class StatusPill(tk.Label):
    def __init__(self, master: tk.Misc, text: str, status: Optional[str] = None, small: bool = False) -> None:
        color = STATUS_COLORS.get(status or text, COLORS["accent"])
        font = FONTS["small_bold"] if small else FONTS["body_bold"]
        super().__init__(master, text=ui_text(text), bg=color, fg="#FFFFFF", font=font, padx=10, pady=4)


class Chip(tk.Label):
    def __init__(self, master: tk.Misc, text: str, variant: str = "blue") -> None:
        palette = {
            "blue": (COLORS["accent_soft"], COLORS["accent_line"]),
            "gray": (COLORS["bg_card_2"], COLORS["text_sub"]),
            "success": ("#0F2A1A", COLORS["success"]),
            "warning": ("#2B210B", COLORS["warning"]),
            "danger": ("#2A1113", COLORS["danger"]),
        }
        bg, fg = palette.get(variant, palette["blue"])
        super().__init__(master, text=ui_text(text), bg=bg, fg=fg, font=FONTS["small_bold"], padx=8, pady=3)


class LabeledValue(tk.Frame):
    def __init__(self, master: tk.Misc, label: str, value: str, value_color: Optional[str] = None, bg: Optional[str] = None) -> None:
        background = bg or COLORS["bg_card"]
        super().__init__(master, bg=background)
        self.columnconfigure(1, weight=1)
        tk.Label(self, text=ui_text(label), bg=background, fg=COLORS["text_sub"], font=FONTS["body"], anchor="w").grid(row=0, column=0, sticky="w")
        tk.Label(
            self,
            text=ui_text(value),
            bg=background,
            fg=value_color or COLORS["text_main"],
            font=FONTS["body"],
            anchor="e",
            justify="right",
            wraplength=360,
        ).grid(row=0, column=1, sticky="e", padx=(10, 0))


class MetricRow(tk.Frame):
    def __init__(self, master: tk.Misc, icon: str, label: str, value: int | str, color: str) -> None:
        super().__init__(master, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
        self.grid_columnconfigure(1, weight=1)
        tk.Label(self, text=icon, bg=COLORS["bg_card_2"], fg=color, font=FONTS["body_bold"], width=2).grid(row=0, column=0, sticky="w", padx=(10, 4), pady=8)
        tk.Label(self, text=ui_text(label), bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["body"]).grid(row=0, column=1, sticky="w", pady=8)
        tk.Label(self, text=ui_text(str(value)), bg=COLORS["bg_card_2"], fg=color, font=FONTS["number"]).grid(row=0, column=2, sticky="e", padx=(8, 12), pady=6)


class StepItem(tk.Frame):
    def __init__(self, master: tk.Misc, title: str, state_text: str, status: str) -> None:
        super().__init__(master, bg=COLORS["bg_card"])
        color = STATUS_COLORS.get(status, COLORS["readonly"])
        tk.Label(self, text="●", bg=COLORS["bg_card"], fg=color, font=FONTS["body_bold"]).pack(side="left")
        tk.Label(self, text=ui_text(title), bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["body"]).pack(side="left", padx=(8, 4))
        tk.Label(self, text=ui_text(state_text), bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(side="left")


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
def make_button(master: tk.Misc, text: str, command: Callable[[], None], variant: str = "secondary", **kwargs) -> tk.Button:
    style = BUTTON_STYLES.get(variant, BUTTON_STYLES["secondary"])
    return tk.Button(
        master,
        text=ui_text(text),
        command=command,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=kwargs.pop("padx", DIMENS["button_pad_x"]),
        pady=kwargs.pop("pady", DIMENS["button_pad_y"]),
        font=kwargs.pop("font", FONTS["body"]),
        **style,
        **kwargs,
    )


def make_section_title(master: tk.Misc, text: str) -> tk.Label:
    return tk.Label(master, text=ui_text(text), bg=COLORS["bg_root"], fg=COLORS["text_main"], font=FONTS["page_title"])


def make_hint(master: tk.Misc, text: str, bg: Optional[str] = None, wraplength: int = 420) -> tk.Label:
    return tk.Label(master, text=ui_text(text), bg=bg or COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=wraplength, justify="left")


def make_readonly_banner(master: tk.Misc, text: str) -> tk.Frame:
    frame = tk.Frame(master, bg=COLORS["accent_soft"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
    frame.grid_columnconfigure(1, weight=1)
    tk.Label(frame, text="◆", bg=COLORS["accent_soft"], fg=COLORS["accent_line"], font=FONTS["small_bold"]).grid(row=0, column=0, padx=(10, 6), pady=7)
    tk.Label(frame, text=ui_text(text), bg=COLORS["accent_soft"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=720, justify="left", anchor="w").grid(row=0, column=1, sticky="ew", pady=7)
    return frame

class Tooltip:
    """Small hover tooltip for Tool/Skill descriptions.

    Display-only widget; it never submits actions or grants execution rights.
    """

    def __init__(self, widget: tk.Widget, text: str, *, delay_ms: int = 350, wraplength: int = 420) -> None:
        self.widget = widget
        self.text = ui_text(text)
        self.delay_ms = delay_ms
        self.wraplength = wraplength
        self._after_id: str | None = None
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event: tk.Event | None = None) -> None:
        self._cancel()
        try:
            self._after_id = self.widget.after(self.delay_ms, self._show)
        except tk.TclError:
            self._after_id = None

    def _cancel(self) -> None:
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
        self._after_id = None

    def _show(self) -> None:
        self._cancel()
        if self._tip is not None or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 18
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
            tip = tk.Toplevel(self.widget)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{x}+{y}")
            tip.configure(bg=COLORS["border"])
            label = tk.Label(
                tip,
                text=self.text,
                bg=COLORS["bg_popup"],
                fg=COLORS["text_main"],
                font=FONTS["small"],
                justify="left",
                wraplength=self.wraplength,
                padx=10,
                pady=8,
                relief="flat",
            )
            label.pack(fill="both", expand=True, padx=1, pady=1)
            self._tip = tip
        except tk.TclError:
            self._tip = None

    def _hide(self, _event: tk.Event | None = None) -> None:
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except tk.TclError:
                pass
            self._tip = None
