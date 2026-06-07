from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from .theme import BUTTON_STYLES, COLORS, DIMENS, FONTS, STATUS_COLORS


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


# ---------------------------------------------------------------------------
# Primitive components
# ---------------------------------------------------------------------------
class Card(tk.Frame):
    """极夜卡片组件。

    tkinter 没有原生圆角和 CSS 阴影；FE.01 使用统一背景、细描边、标题层级和留白，
    保持未来迁移到自绘 Canvas / ttk theme 时的组件边界稳定。
    """

    def __init__(self, master: tk.Misc, title: str = "", subtitle: str = "", **kwargs) -> None:
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
            tk.Label(header, text=title, bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["card_title"]).grid(row=0, column=0, sticky="w")
            if subtitle:
                tk.Label(header, text=subtitle, bg=COLORS["bg_card"], fg=COLORS["text_weak"], font=FONTS["small"]).grid(row=1, column=0, sticky="w", pady=(3, 0))


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
        super().__init__(master, text=text, bg=color, fg="#FFFFFF", font=font, padx=10, pady=4)


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
        super().__init__(master, text=text, bg=bg, fg=fg, font=FONTS["small_bold"], padx=8, pady=3)


class LabeledValue(tk.Frame):
    def __init__(self, master: tk.Misc, label: str, value: str, value_color: Optional[str] = None, bg: Optional[str] = None) -> None:
        background = bg or COLORS["bg_card"]
        super().__init__(master, bg=background)
        self.columnconfigure(1, weight=1)
        tk.Label(self, text=label, bg=background, fg=COLORS["text_sub"], font=FONTS["body"]).grid(row=0, column=0, sticky="w")
        tk.Label(
            self,
            text=value,
            bg=background,
            fg=value_color or COLORS["text_main"],
            font=FONTS["body"],
            anchor="e",
        ).grid(row=0, column=1, sticky="e", padx=(10, 0))


class MetricRow(tk.Frame):
    def __init__(self, master: tk.Misc, icon: str, label: str, value: int | str, color: str) -> None:
        super().__init__(master, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
        self.grid_columnconfigure(1, weight=1)
        tk.Label(self, text=icon, bg=COLORS["bg_card_2"], fg=color, font=FONTS["body_bold"], width=2).grid(row=0, column=0, sticky="w", padx=(10, 4), pady=8)
        tk.Label(self, text=label, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["body"]).grid(row=0, column=1, sticky="w", pady=8)
        tk.Label(self, text=str(value), bg=COLORS["bg_card_2"], fg=color, font=FONTS["number"]).grid(row=0, column=2, sticky="e", padx=(8, 12), pady=6)


class StepItem(tk.Frame):
    def __init__(self, master: tk.Misc, title: str, state_text: str, status: str) -> None:
        super().__init__(master, bg=COLORS["bg_card"])
        color = STATUS_COLORS.get(status, COLORS["readonly"])
        tk.Label(self, text="●", bg=COLORS["bg_card"], fg=color, font=FONTS["body_bold"]).pack(side="left")
        tk.Label(self, text=title, bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["body"]).pack(side="left", padx=(8, 4))
        tk.Label(self, text=state_text, bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(side="left")


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
def make_button(master: tk.Misc, text: str, command: Callable[[], None], variant: str = "secondary", **kwargs) -> tk.Button:
    style = BUTTON_STYLES.get(variant, BUTTON_STYLES["secondary"])
    return tk.Button(
        master,
        text=text,
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
    return tk.Label(master, text=text, bg=COLORS["bg_root"], fg=COLORS["text_main"], font=FONTS["page_title"])


def make_hint(master: tk.Misc, text: str, bg: Optional[str] = None, wraplength: int = 420) -> tk.Label:
    return tk.Label(master, text=text, bg=bg or COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=wraplength, justify="left")


def make_readonly_banner(master: tk.Misc, text: str) -> tk.Frame:
    frame = tk.Frame(master, bg=COLORS["accent_soft"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
    frame.grid_columnconfigure(1, weight=1)
    tk.Label(frame, text="◆", bg=COLORS["accent_soft"], fg=COLORS["accent_line"], font=FONTS["small_bold"]).grid(row=0, column=0, padx=(10, 6), pady=7)
    tk.Label(frame, text=text, bg=COLORS["accent_soft"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=0, column=1, sticky="w", pady=7)
    return frame


class CollapsibleFrame(tk.Frame):
    """可折叠内容块，点击标题展开/收起。"""

    def __init__(self, master: tk.Misc, title: str, content: str, *, collapsed: bool = True, max_lines: int = 4) -> None:
        super().__init__(master, bg=COLORS["bg_card"])
        self.grid_columnconfigure(0, weight=1)
        self._collapsed = collapsed
        self._title = title
        self._full_content = content
        self._max_lines = max_lines
        # 标题栏（可点击）
        self._header = tk.Frame(self, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
        self._header.grid(row=0, column=0, sticky="ew", pady=(4, 0))
        self._header.grid_columnconfigure(0, weight=1)
        self._toggle_icon = tk.Label(self._header, text="▶" if collapsed else "▼", bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], padx=8, pady=4)
        self._toggle_icon.grid(row=0, column=0, sticky="w")
        tk.Label(self._header, text=title, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=0, column=1, sticky="w", padx=(0, 8))
        # 内容区
        self._body = tk.Frame(self, bg=COLORS["bg_card"])
        self._body.grid_columnconfigure(0, weight=1)
        self._text = tk.Text(self._body, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", wrap="none", font=FONTS["mono"], padx=8, pady=6, height=1, width=60)
        self._text.insert("1.0", content)
        self._text.configure(state="disabled")
        # 绑定点击
        for widget in (self._header, self._toggle_icon):
            widget.bind("<Button-1>", lambda _e: self._toggle())
        self._apply_state()

    def _apply_state(self) -> None:
        if self._collapsed:
            self._body.grid_forget()
            self._toggle_icon.configure(text="▶")
        else:
            self._body.grid(row=1, column=0, sticky="ew", pady=(2, 6))
            line_count = min(self._full_content.count("\n") + 1, 20)
            self._text.configure(height=max(3, min(line_count, 12)))
            self._toggle_icon.configure(text="▼")

    def _toggle(self) -> None:
        self._collapsed = not self._collapsed
        self._apply_state()
