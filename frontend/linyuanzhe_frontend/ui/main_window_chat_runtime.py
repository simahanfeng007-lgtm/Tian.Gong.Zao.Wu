from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Dict, Iterable, List

from linyuanzhe_frontend.contracts.product_identity import PRODUCT_IDENTITY
from linyuanzhe_frontend.contracts.model_settings import DEFAULT_MODEL_CATALOG, filter_model_catalog, sanitize_runtime_settings
from linyuanzhe_frontend.contracts.provider_settings import provider_readiness_from_public_projection
from linyuanzhe_frontend.contracts.work_modes import work_mode_labels, work_mode_label
from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot, StepSummary, CHAT_MESSAGE_DISPLAY_LIMIT, CHAT_USER_INPUT_LIMIT, digest_text, safe_chat_text, safe_text
from linyuanzhe_frontend.version_info import PROVIDER_CONFIG_SCHEMA_VERSION
from .theme import COLORS, DIMENS, FONTS, STATUS_COLORS, THEME_PROFILES
from .widgets import Card, Chip, MetricRow, StepItem, LabeledValue, StatusPill, make_button, make_hint, make_readonly_banner, make_section_title, make_vertical_scrollbar


_INTERNAL_RENDER_SIGNAL_RE = re.compile(
    r"^\s*(return_analysis|return_code|model_chat|tool_call_raw|assistant_analysis|raw_delta|debug_payload|internal_signal)\b\s*[:：=]",
    re.I,
)


def _strip_internal_render_lines(text: str) -> str:
    kept: list[str] = []
    for line in str(text or "").split("\n"):
        if _INTERNAL_RENDER_SIGNAL_RE.search(line):
            continue
        kept.append(line)
    return "\n".join(kept)



def _looks_like_mojibake_or_binary_render_text(text: str) -> bool:
    sample = str(text or "")[:4000]
    if not sample:
        return False
    replacement = sample.count("\ufffd") + sample.count("�")
    box_like = sample.count("□") + sample.count("�")
    controls = sum(1 for ch in sample if ord(ch) < 32 and ch not in "\n\r\t")
    if replacement >= 3 or box_like >= 6 or controls >= 3:
        return True
    if re.search(r"(?:\\x[0-9a-fA-F]{2}){4,}|PK\x03\x04|%PDF-|\x00", sample):
        return True
    printable = sum(1 for ch in sample if ch.isprintable() or ch in "\n\r\t")
    return len(sample) >= 120 and printable / max(1, len(sample)) < 0.86


def _placeholder_for_hidden_tool_payload() -> str:
    return (
        "工具已返回结果，但原始内容包含不可直接展示的二进制/编码异常片段。\n"
        "主会话已隐藏原始输出，避免乱码污染；诊断/审计仍保留脱敏摘要。\n"
        "如需读取 Office/PDF/图片/未知编码文件，请使用文档解析能力或先转为 UTF-8 文本。"
    )

def enhance_conversation_readability(raw_text: Any, *, is_assistant: bool = False) -> str:
    """Normalize dense transcript text into a more readable chat presentation.

    This is a UI-only rendering helper. It never changes Runtime payloads or
    PromptCore input. The goal is to make compact model prose easier to read in
    the desktop transcript, especially for Chinese long-form answers that place
    many list items on a single line.
    """
    text = safe_chat_text(raw_text, CHAT_MESSAGE_DISPLAY_LIMIT)
    if not text:
        return ""
    normalized = _strip_internal_render_lines(text.replace('\r\n', '\n').replace('\r', '\n')).strip()
    if is_assistant and _looks_like_mojibake_or_binary_render_text(normalized):
        return _placeholder_for_hidden_tool_payload()
    if not is_assistant:
        return normalized

    if '```' in normalized or '~~~' in normalized:
        # Preserve authored markdown / code layouts verbatim.
        return normalized

    # Light whitespace cleanup while preserving existing paragraph breaks.
    normalized = re.sub(r'[\t\f\v]+', ' ', normalized)
    normalized = re.sub(r'\u3000+', ' ', normalized)
    normalized = re.sub(r' {2,}', ' ', normalized)

    # Convert inline list separators into markdown bullets when several items are
    # packed onto one line, e.g. "包括： - A - B - C" or "包括： · A · B · C".
    inline_bullet_markers = len(re.findall(r'\s[-•·●▪▸▹]\s+', normalized))
    if '\n' not in normalized and inline_bullet_markers >= 3:
        normalized = re.sub(r'([：:])\s*[-•·●▪▸▹]\s+', r'\1\n\n- ', normalized, count=1)
        normalized = re.sub(r'\s[-•·●▪▸▹]\s+', '\n- ', normalized)

    # For dense long prose, insert paragraph breaks before common discourse
    # transitions so the transcript reads like UI content rather than a wall.
    if len(normalized) >= 90:
        transition_words = [
            '如果', '另外', '此外', '同时', '然后', '接着', '最后',
            '作为', '总结', '注意', '建议', '下一步', '若你', '如果你',
        ]
        pattern = r'([。！？；])\s*(?=(' + '|'.join(map(re.escape, transition_words)) + r'))'
        normalized = re.sub(pattern, r'\1\n\n', normalized)
        normalized = re.sub(r'(\n- [^\n]+?)\s+(?=(作为|如果|另外|此外|总结|建议|注意|下一步))', r'\1\n\n', normalized)

    # If a long paragraph still has no breaks, gently split by terminal punctuation.
    lines: list[str] = []
    for paragraph in normalized.split('\n\n'):
        chunk = paragraph.strip()
        if not chunk:
            continue
        if ('\n' not in chunk and len(chunk) > 140 and '- ' not in chunk and not re.search(r'^#{1,3}\s', chunk)):
            parts = [part.strip() for part in re.split(r'(?<=[。！？；])\s*', chunk) if part.strip()]
            if len(parts) >= 2:
                chunk = '\n'.join(parts)
        lines.append(chunk)

    normalized = '\n\n'.join(lines)
    normalized = re.sub(r'\n{3,}', '\n\n', normalized).strip()
    return normalized


class ChatRuntimeMixin:
    def _build_chat_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        """Homepage: chat-first desktop workspace.

        STEP31Q keeps the main conversation dominant and makes 模型服务就绪状态明确。运行时详情
        move into one collapsible 会话信息 panel so the homepage no longer reads as
        an operations dashboard.
        """
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=0)
        root.grid_rowconfigure(0, weight=1)

        current_width = self._current_window_width() if hasattr(self, "_current_window_width") else 1280
        show_side = bool(self.session_info_expanded or current_width >= 1360)
        self._chat_side_panel_visible = show_side

        main = tk.Frame(root, bg=COLORS["bg_root"])
        main.grid(row=0, column=0, sticky="nsew", padx=(DIMENS["page_pad"], DIMENS["page_pad"] if not show_side else 6), pady=DIMENS["page_pad"])
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)

        chat_card = Card(main, "会话")
        chat_card.grid(row=0, column=0, sticky="nsew")
        chat_card.grid_columnconfigure(0, weight=1)
        self._populate_chat_card(chat_card, s)

        if show_side:
            side_width = DIMENS["right_col_w"] if self.session_info_expanded else 108
            side = tk.Frame(root, bg=COLORS["bg_root"], width=side_width)
            side.grid(row=0, column=1, sticky="ns", padx=(6, DIMENS["page_pad"]), pady=DIMENS["page_pad"])
            side.grid_propagate(False)
            side.grid_columnconfigure(0, weight=1)
            side.grid_rowconfigure(0, weight=1)
            self._build_session_info_panel(side, s)

    def _toggle_session_info_panel(self) -> None:
        self.session_info_expanded = not self.session_info_expanded
        self.show_page("chat")

    def _build_session_info_panel(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        if not self.session_info_expanded:
            rail = tk.Frame(root, bg=COLORS["bg_card"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            rail.grid(row=0, column=0, sticky="nsew")
            rail.grid_columnconfigure(0, weight=1)
            tk.Button(
                rail,
                text="会话\n信息",
                command=self._toggle_session_info_panel,
                bg=COLORS["bg_card_2"],
                fg=COLORS["text_main"],
                activebackground=COLORS["selected"],
                activeforeground=COLORS["text_main"],
                relief="flat",
                padx=8,
                pady=10,
                cursor="hand2",
                font=FONTS["body_bold"],
            ).grid(row=0, column=0, sticky="ew", padx=8, pady=(10, 8))
            StatusPill(rail, self._status_short(s.current_task_status), s.current_task_status, small=True).grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
            tk.Label(
                rail,
                text=self._home_mode_label(s),
                bg=COLORS["bg_card"],
                fg=COLORS["text_weak"],
                font=FONTS["small"],
                wraplength=78,
                justify="center",
            ).grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 10))
            return

        card = Card(root, "会话信息")
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(4, 14))
        body.grid_columnconfigure(0, weight=1)

        header = tk.Frame(body, bg=COLORS["bg_card"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(0, weight=1)
        StatusPill(header, self._status_short(s.current_task_status), s.current_task_status, small=True).grid(row=0, column=0, sticky="w")
        tk.Button(header, text="收起", command=self._toggle_session_info_panel, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=8, pady=4).grid(row=0, column=1, sticky="e")

        snap = s.task_snapshot
        rows = [
            ("模式", self._home_mode_label(s)),
            ("阶段", safe_text(snap.current_stage or s.current_stage, 42)),
            ("质量门", safe_text(getattr(s, "gate_status", s.quality_gate_status), 32)),
            ("审计", safe_text(getattr(s, "audit_id", s.evidence_ref), 32) or "无"),
        ]
        for idx, (label, value) in enumerate(rows, start=1):
            LabeledValue(body, label, value).grid(row=idx, column=0, sticky="ew", pady=4)

        hint = self._home_continue_hint(s)
        make_hint(body, hint, bg=COLORS["bg_card"], wraplength=290).grid(row=5, column=0, sticky="ew", pady=(10, 6))

        guide = getattr(s, "conversation_guide", None)
        actions = list(getattr(guide, "recommended_actions", []) or [])[:3]
        if actions:
            for offset, action in enumerate(actions, start=6):
                tk.Button(
                    body,
                    text=safe_text(action, 52),
                    command=lambda text=action: self._insert_guided_prompt(text),
                    bg=COLORS["bg_card_2"],
                    fg=COLORS["text_main"],
                    relief="flat",
                    anchor="w",
                    padx=8,
                    pady=5,
                ).grid(row=offset, column=0, sticky="ew", pady=2)
            next_row = 6 + len(actions)
        else:
            next_row = 6

        buttons = tk.Frame(body, bg=COLORS["bg_card"])
        buttons.grid(row=next_row, column=0, sticky="ew", pady=(12, 0))
        tk.Button(buttons, text="任务", command=lambda: self.show_page("sessions"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).pack(side="left", padx=(0, 6))
        tk.Button(buttons, text="质量门", command=self._show_quality_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).pack(side="left", padx=(0, 6))
        tk.Button(buttons, text="审计", command=self._show_audit_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).pack(side="left")

    def _status_short(self, status: str) -> str:
        return {
            "READY": "就绪",
            "RUNNING": "运行",
            "COMPLETED": "完成",
            "PENDING": "待确认",
            "BLOCKED": "阻断",
            "FAILED": "失败",
            "DISCONNECTED": "断开",
        }.get(safe_text(status, 32).upper(), safe_text(status or "就绪", 12))

    def _home_mode_label(self, s: RuntimeSnapshot) -> str:
        readiness = self._provider_readiness_public(self._provider_public_from_snapshot(s))
        if readiness.get("readiness") == "ready":
            model = safe_text(getattr(s, "provider_model", "") or getattr(s, "model_provider", ""), 28)
            return f"真实模型 · {model}" if model else "真实模型就绪"
        if readiness.get("readiness") == "forced_mock":
            return "未配置模型接口"
        if readiness.get("readiness") == "missing_credentials":
            return "缺少模型接口配置"
        if readiness.get("readiness") == "error":
            return "模型服务异常"
        mode = safe_text(getattr(s, "provider_config_state", "") or getattr(s, "source_kind", ""), 28)
        if "mock" in mode.lower() or "mock" in safe_text(getattr(s, "connection_status", ""), 80).lower():
            return "未配置模型接口"
        return safe_text(getattr(s, "runtime_status", "就绪"), 28)

    def _home_continue_hint(self, s: RuntimeSnapshot) -> str:
        readiness = self._provider_readiness_public(self._provider_public_from_snapshot(s))
        if bool(getattr(s.task_snapshot, "waiting_user_confirmation", False)):
            return "当前等待确认。打开质量门详情后再决定允许或拒绝。"
        if not bool(getattr(s, "quality_allow_continue", True)):
            return "质量门显示不可继续。请查看摘要后处理阻断原因。"
        if readiness.get("readiness") != "ready":
            return safe_text(readiness.get("message", "尚未配置模型接口。请进入设置页填写服务地址和接口密钥，保存后即可启用真实模型。"), 220)
        return "模型服务就绪，可继续输入任务。详细执行链与审计已下沉，不占用首页。"

    def _populate_chat_card(self, card: Card, s: RuntimeSnapshot) -> None:
        show_task_flow = self._show_task_flow_enabled()
        content_row = 1
        if show_task_flow:
            self._populate_run_workbench_strip(card, s)
            content_row = 2

        # L6.72.52：正文区所在行必须动态获得伸缩权。
        # 旧版固定 row=2；当任务流程关闭时正文在 row=1、输入栏在 row=2，
        # 会导致输入区抢占高度，出现“会话展示不全/正文被压缩”。
        for row in range(0, 5):
            try:
                card.grid_rowconfigure(row, weight=1 if row == content_row else 0)
            except tk.TclError:
                pass

        body_wrap = tk.Frame(card, bg=COLORS["bg_card"])
        body_wrap.grid(row=content_row, column=0, sticky="nsew", padx=12, pady=(2, 8))
        body_wrap.grid_columnconfigure(0, weight=1)
        body_wrap.grid_rowconfigure(0, weight=1)

        body = tk.Text(
            body_wrap,
            bg=COLORS["bg_card"],
            fg=COLORS["text_main"],
            insertbackground=COLORS["text_main"],
            relief="flat",
            wrap="word",
            font=FONTS["body"],
            padx=10,
            pady=7,
            borderwidth=0,
            highlightthickness=0,
        )
        body.grid(row=0, column=0, sticky="nsew")
        scrollbar = make_vertical_scrollbar(body_wrap, body.yview, variant="chat")
        scrollbar.grid(row=0, column=1, sticky="ns")
        body.configure(yscrollcommand=scrollbar.set)
        body.bind("<Button-3>", self._show_message_context_menu, add="+")
        body.bind("<<Copy>>", self._copy_selected_chat_text_event, add="+")
        body.bind("<Control-c>", self._copy_selected_chat_text_event, add="+")
        body.bind("<Command-c>", self._copy_selected_chat_text_event, add="+")
        body.bind("<Double-Button-1>", lambda _event: None, add="+")
        self._chat_body_widget = body
        self._chat_render_signatures = []
        self._new_message_button = tk.Button(body_wrap, text="↓ 新消息", command=self._scroll_chat_to_bottom_from_button, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=10, pady=4)
        self._render_chat_messages_into(body, s, auto_scroll=True)

        input_shell = tk.Frame(card, bg=COLORS["bg_card"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
        input_shell.grid(row=content_row + 1, column=0, sticky="ew", padx=12, pady=(0, 8))
        input_shell.grid_columnconfigure(1, weight=1)

        # L6.72.42: 输入区左侧控制固定两行，和输入框/发送列对齐。
        action_col = tk.Frame(input_shell, bg=COLORS["bg_card"], width=104)
        action_col.grid(row=0, column=0, sticky="ns", padx=(8, 8), pady=6)
        action_col.grid_propagate(False)
        action_col.grid_columnconfigure(0, weight=1)
        mode_combo = ttk.Combobox(action_col, textvariable=self.work_mode_var, values=work_mode_labels(), width=7, state="readonly")
        mode_combo.grid(row=0, column=0, sticky="ew", pady=(0, 5), ipady=1)
        mode_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_work_mode_changed_frontend_only(), add="+")
        tk.Button(action_col, text="附件", command=self._request_file_transfer_from_dialog, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=8, pady=4).grid(row=1, column=0, sticky="ew")

        input_area = tk.Frame(input_shell, bg=COLORS["bg_input"], highlightbackground=COLORS["border_soft"], highlightthickness=1, height=74)
        input_area.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=6)
        input_area.grid_columnconfigure(0, weight=1)
        input_area.grid_propagate(False)
        self.input_text = tk.Text(
            input_area,
            height=2,
            bg=COLORS["bg_input"],
            fg=COLORS["text_main"],
            insertbackground=COLORS["text_main"],
            relief="flat",
            wrap="word",
            font=FONTS["body"],
            padx=12,
            pady=7,
            borderwidth=0,
            highlightthickness=0,
        )
        self.input_text.grid(row=0, column=0, sticky="nsew")
        input_area.grid_rowconfigure(0, weight=1)
        self.input_placeholder_label = tk.Label(
            input_area,
            text="输入消息。Enter 发送；Shift+Enter 换行；工作模式才启动任务流程。",
            bg=COLORS["bg_input"],
            fg=COLORS["text_weak"],
            font=FONTS["small"],
            padx=0,
            pady=0,
        )
        self.input_placeholder_label.place(x=14, y=12)
        self.input_placeholder_label.bind("<Button-1>", lambda _event: self._focus_chat_input_from_placeholder(), add="+")
        self.input_text.bind("<Return>", self._send_message_from_event)
        self.input_text.bind("<KeyPress>", self._track_ime_input_event, add="+")
        self.input_text.bind("<KeyRelease>", self._track_ime_input_event, add="+")
        self.input_text.bind("<Shift-Return>", self._insert_newline_from_event)
        self.input_text.bind("<Key>", self._hide_input_placeholder, add="+")
        self.input_text.bind("<FocusIn>", self._sync_input_placeholder, add="+")
        self.input_text.bind("<FocusOut>", self._sync_input_placeholder, add="+")
        self.input_text.bind("<<Modified>>", self._sync_input_placeholder, add="+")
        self._sync_input_placeholder()

        send_col = tk.Frame(input_shell, bg=COLORS["bg_card"])
        send_col.grid(row=0, column=2, sticky="nsew", padx=(0, 8), pady=6)
        tk.Button(send_col, text=self._current_work_mode_button_text(), command=self._send_message, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=16, pady=7).pack(side="top", fill="x")
        ctrl_row = tk.Frame(send_col, bg=COLORS["bg_card"])
        ctrl_row.pack(side="top", fill="x", pady=(5, 0))
        for col, (label, command) in enumerate([
            ("引导", lambda: self._insert_guided_prompt(self._primary_guided_prompt(self.snapshot))),
            ("中断", self._request_task_interrupt),
            ("新对话", self._new_task_frontend_only),
        ]):
            ctrl_row.grid_columnconfigure(col, weight=1, uniform="input_ctrl")
            tk.Button(
                ctrl_row, text=label, command=command, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"],
                relief="flat", padx=6, pady=3, font=FONTS["small"],
            ).grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 3, 0))
        status_row = tk.Frame(card, bg=COLORS["bg_card"])
        status_row.grid(row=content_row + 2, column=0, sticky="ew", padx=14, pady=(0, 8))
        status_row.grid_columnconfigure(0, weight=1)
        tk.Label(status_row, textvariable=self.stream_status_var, bg=COLORS["bg_card"], fg=COLORS["text_weak"], font=FONTS["small"]).grid(row=0, column=0, sticky="w")
        tk.Label(status_row, textvariable=self.live_stream_var, bg=COLORS["bg_card"], fg=COLORS["accent_line"], font=FONTS["small_bold"]).grid(row=0, column=1, sticky="e")
        self._sync_live_stream_indicator(self.snapshot, finished=False)


    def _populate_run_workbench_strip(self, card: Card, s: RuntimeSnapshot) -> None:
        """Compact Run 工作台。L6.72.44 允许纯聊天表面隐藏流程展示。"""
        if not self._show_task_flow_enabled():
            return
        strip = tk.Frame(card, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
        strip.grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 6))
        strip.grid_columnconfigure(2, weight=1)
        state = safe_text(getattr(s, "run_workbench_state", "idle"), 32) or "idle"
        label = safe_text(getattr(s, "run_status_label", "待机"), 32) or "待机"
        color_map = {
            "idle": COLORS["text_sub"],
            "submitting": COLORS["warning"],
            "accepted": COLORS["accent"],
            "planning": COLORS["accent"],
            "waiting_approval": COLORS["warning"],
            "tool_running": COLORS["accent"],
            "streaming": COLORS["accent"],
            "reconnecting": COLORS["warning"],
            "recoverable": COLORS["warning"],
            "completed": COLORS["success"],
            "failed": COLORS["danger"],
            "cancelled": COLORS["readonly"],
        }
        state_color = color_map.get(state, COLORS["text_sub"])
        tk.Label(strip, text="任务工作台", bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["small_bold"]).grid(row=0, column=0, sticky="w", padx=(10, 6), pady=5)
        tk.Label(strip, text=f"● {label}", bg=COLORS["bg_card_2"], fg=state_color, font=FONTS["small_bold"]).grid(row=0, column=1, sticky="w", padx=(0, 8), pady=5)

        buttons = tk.Frame(strip, bg=COLORS["bg_card_2"])
        buttons.grid(row=0, column=3, sticky="e", padx=(6, 8), pady=4)
        compact_buttons = [
            ("信息", self._toggle_session_info_panel, COLORS["text_sub"]),
            ("重连", self._request_runtime_reconnect, COLORS["text_sub"]),
            ("停止", self._request_task_stop, COLORS["danger"]),
            ("诊断", self._copy_run_diagnostic, COLORS["text_sub"]),
        ]
        for idx, (label_text, command, fg) in enumerate(compact_buttons):
            tk.Button(
                buttons,
                text=label_text,
                command=command,
                bg=COLORS["bg_card"],
                fg=fg,
                relief="flat",
                padx=8,
                pady=2,
                font=FONTS["small"],
            ).pack(side="left", padx=(0 if idx == 0 else 4, 0))


    def _chat_should_auto_scroll(self, body: tk.Text | None = None) -> bool:
        widget = body or getattr(self, "_chat_body_widget", None)
        if widget is None:
            return True
        try:
            first, last = widget.yview()
            return last >= 0.985
        except tk.TclError:
            return True

    def _show_new_message_button(self) -> None:
        btn = getattr(self, "_new_message_button", None)
        if btn is None:
            return
        try:
            btn.place(relx=1.0, rely=1.0, x=-18, y=-18, anchor="se")
        except tk.TclError as exc:
            self._record_ui_warning("new_message_button_show", exc, 80)

    def _hide_new_message_button(self) -> None:
        btn = getattr(self, "_new_message_button", None)
        if btn is None:
            return
        try:
            btn.place_forget()
        except tk.TclError as exc:
            self._record_ui_warning("new_message_button_hide", exc, 80)

    def _scroll_chat_to_bottom_from_button(self) -> None:
        self._force_chat_scroll_to_end()
        self._hide_new_message_button()

    def _show_message_context_menu(self, event: tk.Event) -> str:
        menu = tk.Menu(self, tearoff=0, bg=COLORS["bg_card"], fg=COLORS["text_main"], activebackground=COLORS["selected"], activeforeground=COLORS["text_main"])
        selected = self._get_selected_chat_text()
        menu.add_command(label="复制选中内容" if selected else "复制最后消息", command=self._copy_selected_or_last_message)
        menu.add_command(label="重新发送", command=self._resend_last_user_message)
        menu.add_command(label="引用回复", command=self._quote_selected_or_last_message)
        menu.add_separator()
        menu.add_command(label="复制最后代码块", command=self._copy_last_code_block)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    def _get_selected_chat_text(self) -> str:
        widget = getattr(self, "_chat_body_widget", None)
        if widget is None:
            return ""
        try:
            return safe_chat_text(widget.get("sel.first", "sel.last"), 12000)
        except tk.TclError:
            return ""

    def _copy_selected_chat_text_event(self, _event: tk.Event | None = None) -> str | None:
        text = self._get_selected_chat_text()
        if not text:
            return None
        try:
            self.clipboard_clear(); self.clipboard_append(text)
            self.stream_status_var.set("已复制选中内容。")
        except tk.TclError as exc:
            self._record_ui_warning("copy_selected_chat_text", exc, 80)
        return "break"

    def _copy_selected_or_last_message(self) -> None:
        text = self._get_selected_chat_text()
        if not text:
            messages = list(getattr(self.snapshot, "chat_messages", []) or [])
            if messages:
                text = safe_chat_text(getattr(messages[-1], "text", ""), CHAT_MESSAGE_DISPLAY_LIMIT)
        if text:
            try:
                self.clipboard_clear(); self.clipboard_append(text)
                self.stream_status_var.set("已复制消息文本。")
            except tk.TclError as exc:
                self._record_ui_warning("copy_message", exc, 80)

    def _resend_last_user_message(self) -> None:
        for msg in reversed(list(getattr(self.snapshot, "chat_messages", []) or [])):
            if safe_text(getattr(msg, "role", ""), 32).lower() in {"user", "human"}:
                text = safe_chat_text(getattr(msg, "text", ""), CHAT_USER_INPUT_LIMIT)
                if hasattr(self, "input_text"):
                    self.input_text.delete("1.0", "end")
                    self.input_text.insert("1.0", text)
                    self.input_text.focus_set()
                    self._sync_input_placeholder()
                return

    def _quote_selected_or_last_message(self) -> None:
        quote = ""
        widget = getattr(self, "_chat_body_widget", None)
        try:
            if widget is not None:
                quote = widget.get("sel.first", "sel.last")
        except tk.TclError:
            quote = ""
        if not quote:
            messages = list(getattr(self.snapshot, "chat_messages", []) or [])
            if messages:
                quote = safe_chat_text(getattr(messages[-1], "text", ""), 500)
        if hasattr(self, "input_text") and quote:
            self.input_text.insert("1.0", f"> {safe_text(quote, 500)}\n\n")
            self.input_text.focus_set()
            self._sync_input_placeholder()

    def _copy_last_code_block(self) -> None:
        code = ""
        for msg in reversed(list(getattr(self.snapshot, "chat_messages", []) or [])):
            text = safe_chat_text(getattr(msg, "text", ""), CHAT_MESSAGE_DISPLAY_LIMIT)
            matches = re.findall(r"```[^\n]*\n(.*?)```", text, flags=re.S)
            if matches:
                code = matches[-1].strip()
                break
        if not code:
            self.stream_status_var.set("未找到可复制代码块。")
            return
        try:
            self.clipboard_clear(); self.clipboard_append(code)
            self.stream_status_var.set("已复制最后一个代码块。")
        except tk.TclError as exc:
            self._record_ui_warning("copy_last_code", exc, 120)

    def _maybe_show_permission_popup(self, s: RuntimeSnapshot) -> None:
        ticket = self._extract_first_pending_confirmation(s)
        if not ticket:
            return
        ticket_id = safe_text(ticket.get("ticket_id", ""), 80)
        if not ticket_id or ticket_id == getattr(self, "_pending_permission_popup_ticket_id", ""):
            return
        self._pending_permission_popup_ticket_id = ticket_id
        self._show_permission_approval_modal(ticket)

    def _extract_first_pending_confirmation(self, s: RuntimeSnapshot) -> Dict[str, Any]:
        for ticket in list(getattr(s, "pending_confirmations", []) or []):
            if safe_text(ticket.get("frontend_decision", ""), 32):
                continue
            if safe_text(ticket.get("ticket_id", ""), 80):
                return dict(ticket)
        for guard in list(getattr(s, "action_guard_cards", []) or []):
            if bool(getattr(guard, "requires_user_confirmation", False)):
                tid = safe_text(getattr(guard, "ticket_id", ""), 80)
                if tid:
                    return {
                        "ticket_id": tid,
                        "title": safe_text(getattr(guard, "title", "权限申请"), 120),
                        "source": safe_text(getattr(guard, "tool_name", "QualityGate"), 80),
                        "action_summary": safe_text(getattr(guard, "action_summary", "请求执行受控操作"), 240),
                        "impact_scope": safe_text(getattr(guard, "impact_scope", "未提供影响范围"), 240),
                        "risk_level": safe_text(getattr(guard, "risk_level", "中"), 20),
                    }
        return {}

    def _show_permission_approval_modal(self, ticket: Dict[str, Any]) -> None:
        ticket_id = safe_text(ticket.get("ticket_id", ""), 80)
        win = tk.Toplevel(self)
        win.title("权限申请审批")
        win.transient(self)
        win.grab_set()
        win.configure(bg=COLORS["bg_root"])
        win.geometry("520x360")
        win.minsize(480, 320)
        risk = safe_text(ticket.get("risk_level", "中"), 20)
        risk_key = "high" if risk.upper() in {"A4", "A5", "高", "HIGH"} else "medium" if risk.upper() in {"A2", "A3", "中", "MEDIUM"} else "low"
        tk.Label(win, text="权限申请审批", bg=COLORS["bg_root"], fg=COLORS["text_main"], font=FONTS["page_title"]).pack(anchor="w", padx=18, pady=(16, 8))
        body = tk.Frame(win, bg=COLORS["bg_card"], highlightbackground=COLORS["border"], highlightthickness=1)
        body.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        rows = [
            ("请求来源", safe_text(ticket.get("source") or ticket.get("tool_name") or ticket.get("skill_name") or "Runtime / QualityGate", 120)),
            ("请求操作", safe_text(ticket.get("action_summary") or ticket.get("title") or "请求执行受控操作", 260)),
            ("涉及范围", safe_text(ticket.get("impact_scope") or ticket.get("path") or "未提供文件/路径摘要", 260)),
            ("风险等级", risk),
            ("票据", ticket_id),
        ]
        for idx, (label, value) in enumerate(rows):
            fg = STATUS_COLORS.get(risk_key, COLORS["text_main"]) if label == "风险等级" else COLORS["text_main"]
            tk.Label(body, text=label, bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=idx, column=0, sticky="nw", padx=12, pady=(10 if idx == 0 else 5, 0))
            tk.Label(body, text=value, bg=COLORS["bg_card"], fg=fg, font=FONTS["body_bold"] if label == "风险等级" else FONTS["body"], wraplength=350, justify="left").grid(row=idx, column=1, sticky="nw", padx=(10, 12), pady=(10 if idx == 0 else 5, 0))
        btns = tk.Frame(win, bg=COLORS["bg_root"])
        btns.pack(fill="x", padx=18, pady=(0, 16))
        def decide(decision: str) -> None:
            try:
                win.destroy()
            except tk.TclError:
                pass
            if decision == "approve_once":
                self._approve_permission_once(ticket_id)
            elif decision == "approve_session":
                self._approve_permission_session(ticket_id)
            else:
                self._reject_permission(ticket_id)
        tk.Button(btns, text="批准一次", command=lambda: decide("approve_once"), bg=COLORS["success"], fg="#FFFFFF", relief="flat", padx=12, pady=6).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="本次会话始终批准", command=lambda: decide("approve_session"), bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=12, pady=6).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="拒绝", command=lambda: decide("reject"), bg=COLORS["danger"], fg="#FFFFFF", relief="flat", padx=12, pady=6).pack(side="right")
        try:
            win.after(60000, lambda: win.winfo_exists() and decide("reject"))
        except tk.TclError as exc:
            self._record_ui_warning("permission_timeout", exc, 80)

    def _insert_chat_emoji(self, emoji: str) -> None:
        widget = getattr(self, "input_text", None)
        if widget is None:
            return
        try:
            widget.insert("insert", safe_text(emoji, 8))
            widget.focus_set()
            self._sync_input_placeholder()
        except tk.TclError as exc:
            self._record_ui_warning("input_emoji_insert", exc, 120)

    def _primary_guided_prompt(self, s: RuntimeSnapshot) -> str:
        guide = getattr(s, "conversation_guide", None)
        actions = list(getattr(guide, "recommended_actions", []) or []) if guide is not None else []
        for action in actions:
            clean = safe_chat_text(action, 300).strip()
            if clean:
                return clean
        return "继续下一步"

    def _focus_chat_input_from_placeholder(self) -> None:
        widget = getattr(self, "input_text", None)
        if widget is None:
            return
        try:
            widget.focus_set()
            self._hide_input_placeholder()
        except tk.TclError as exc:
            self._record_ui_warning("input_placeholder_focus", exc, 120)

    def _hide_input_placeholder(self, _event: Any | None = None) -> None:
        label = getattr(self, "input_placeholder_label", None)
        if label is not None:
            try:
                label.place_forget()
            except tk.TclError as exc:
                self._record_ui_warning("input_placeholder_hide", exc, 120)

    def _sync_input_placeholder(self, _event: Any | None = None) -> None:
        label = getattr(self, "input_placeholder_label", None)
        widget = getattr(self, "input_text", None)
        if label is None or widget is None:
            return
        try:
            text = widget.get("1.0", "end-1c")
            if text.strip():
                label.place_forget()
            else:
                label.place(x=14, y=12)
            try:
                widget.edit_modified(False)
            except tk.TclError as exc:
                self._record_ui_warning("input_placeholder_modified_flag", exc, 120)
        except tk.TclError as exc:
            self._record_ui_warning("input_placeholder_sync", exc, 120)

    def _chat_message_signature(self, msg: Any) -> tuple[str, str, str, str]:
        chat_text = safe_chat_text(getattr(msg, "text", ""), CHAT_MESSAGE_DISPLAY_LIMIT)
        return (
            safe_text(getattr(msg, "role", "assistant"), 32),
            safe_text(getattr(msg, "label", "临渊者"), 32),
            safe_text(getattr(msg, "time", ""), 32),
            digest_text(chat_text, 24),
        )

    def _chat_dynamic_margins(self) -> tuple[int, int]:
        """Return adaptive message margins for narrow and wide desktop windows.

        Human desktop UI guidance favors resizing without clipping. Earlier
        builds used fixed 220/260px margins, which collapsed the usable chat
        width on 720-1000px windows and made CJK text appear squeezed.
        """
        try:
            width = self._current_window_width()
            width -= self._sidebar_width_for_current_window()
            width -= 80
            if bool(getattr(self, "_chat_side_panel_visible", False)):
                width -= DIMENS["right_col_w"] if self.session_info_expanded else 108
        except Exception:
            width = 900
        width = max(420, width)
        # >1400px chat bubbles should not exceed about 65%; otherwise keep a
        # relaxed 85% bubble width by using a smaller opposite margin.
        factor = 0.35 if width >= 1400 else 0.15
        margin = int(width * factor)
        user_left = max(44, min(300, margin))
        assistant_right = max(36, min(260, margin))
        return user_left, assistant_right

    def _configure_chat_markdown_tags(self, body: tk.Text) -> None:
        body.tag_config("meta", foreground=COLORS["text_sub"], font=FONTS["small"], spacing3=3)
        user_left, assistant_right = self._chat_dynamic_margins()
        body.tag_config("meta_user", foreground=COLORS["text_weak"], font=FONTS["small"], justify="right", lmargin1=user_left, lmargin2=user_left, rmargin=16, spacing1=6, spacing3=2)
        body.tag_config("meta_assistant", foreground=COLORS["text_weak"], font=FONTS["small"], justify="left", lmargin1=16, lmargin2=16, rmargin=assistant_right, spacing1=6, spacing3=2)
        leading = float(getattr(self, "line_height_var", tk.DoubleVar(value=1.8)).get())
        line_extra = max(4, int((leading - 1.0) * 12))
        wrap_line_extra = max(1, int((leading - 1.0) * 6))
        body.tag_config("body", foreground=COLORS["text_main"], font=FONTS.get("chat_body", FONTS["body"]), spacing1=3, spacing2=wrap_line_extra, spacing3=line_extra)
        body.tag_config("bubble_assistant", foreground=COLORS["text_main"], background=COLORS["bg_card_2"], font=FONTS.get("chat_body", FONTS["body"]), lmargin1=18, lmargin2=18, rmargin=assistant_right, spacing1=6, spacing2=wrap_line_extra, spacing3=line_extra + 4)
        body.tag_config("bubble_user", foreground=COLORS["text_main"], background=COLORS["accent_soft"], font=FONTS.get("chat_body", FONTS["body"]), justify="right", lmargin1=user_left, lmargin2=user_left, rmargin=16, spacing1=6, spacing2=wrap_line_extra, spacing3=line_extra + 4)
        body.tag_config("md_heading1", foreground=COLORS["text_main"], font=FONTS["page_title"], spacing1=8, spacing3=6)
        body.tag_config("md_heading2", foreground=COLORS["text_main"], font=FONTS["section_title"], spacing1=6, spacing3=5)
        body.tag_config("md_heading3", foreground=COLORS["text_main"], font=FONTS["card_title"], spacing1=5, spacing3=4)
        body.tag_config("md_heading4", foreground=COLORS["text_main"], font=FONTS["body_bold"], spacing1=4, spacing3=3)
        body.tag_config("md_bold", foreground=COLORS["text_main"], font=FONTS["body_bold"])
        body.tag_config("md_italic", foreground=COLORS["text_sub"], font=FONTS.get("chat_body", FONTS["body"]))
        body.tag_config("md_strike", foreground=COLORS["text_weak"], overstrike=True)
        body.tag_config("md_inline_code", foreground=COLORS["accent_line"], background=COLORS["bg_card_3"], font=FONTS["mono"])
        body.tag_config("md_code_block", foreground=COLORS["text_main"], background=COLORS["bg_input"], font=FONTS["mono"], lmargin1=24, lmargin2=24, rmargin=24, spacing1=3, spacing3=3)
        body.tag_config("md_code_label", foreground=COLORS["text_weak"], background=COLORS["bg_input"], font=FONTS["small_bold"], lmargin1=24, lmargin2=24, spacing1=4, spacing3=2)
        body.tag_config("md_list", foreground=COLORS["text_main"], font=FONTS.get("chat_body", FONTS["body"]), lmargin1=34, lmargin2=50, spacing1=3, spacing2=wrap_line_extra, spacing3=3)
        body.tag_config("md_quote", foreground=COLORS["text_sub"], font=FONTS.get("chat_body", FONTS["body"]), lmargin1=28, lmargin2=42, spacing1=3, spacing2=wrap_line_extra, spacing3=3)
        body.tag_config("md_task_pending", foreground=COLORS["text_main"], font=FONTS.get("chat_body", FONTS["body"]), lmargin1=34, lmargin2=54, spacing1=3, spacing3=3)
        body.tag_config("md_task_done", foreground=COLORS["text_sub"], font=FONTS.get("chat_body", FONTS["body"]), lmargin1=34, lmargin2=54, spacing1=3, spacing3=3)
        body.tag_config("md_table", foreground=COLORS["text_main"], background=COLORS["bg_input"], font=FONTS["mono"], lmargin1=22, lmargin2=22, rmargin=22, spacing1=1, spacing3=1)
        body.tag_config("md_table_header", foreground=COLORS["accent_line"], background=COLORS["bg_input"], font=FONTS["mono"], lmargin1=22, lmargin2=22, rmargin=22, spacing1=4, spacing3=2)
        body.tag_config("md_table_separator", foreground=COLORS["divider"], background=COLORS["bg_input"], font=FONTS["mono"], lmargin1=22, lmargin2=22, rmargin=22, spacing1=1, spacing3=2)
        body.tag_config("md_event", foreground=COLORS["text_main"], background=COLORS["bg_card_3"], font=FONTS.get("chat_body", FONTS["body"]), lmargin1=22, lmargin2=22, rmargin=22, spacing1=4, spacing3=4)
        body.tag_config("md_event_success", foreground=COLORS["success"], background=COLORS["bg_card_3"], font=FONTS["body_bold"], lmargin1=22, lmargin2=22, rmargin=22, spacing1=4, spacing3=4)
        body.tag_config("md_event_warning", foreground=COLORS["warning"], background=COLORS["bg_card_3"], font=FONTS["body_bold"], lmargin1=22, lmargin2=22, rmargin=22, spacing1=4, spacing3=4)
        body.tag_config("md_event_error", foreground=COLORS["danger"], background=COLORS["bg_card_3"], font=FONTS["body_bold"], lmargin1=22, lmargin2=22, rmargin=22, spacing1=4, spacing3=4)
        body.tag_config("codex_card_header", foreground=COLORS["accent_line"], background=COLORS["bg_card_3"], font=FONTS["body_bold"], lmargin1=22, lmargin2=22, rmargin=24, spacing1=8, spacing3=4)
        body.tag_config("codex_card_meta", foreground=COLORS["text_sub"], background=COLORS["bg_card_3"], font=FONTS["small_bold"], lmargin1=22, lmargin2=22, rmargin=24, spacing1=2, spacing3=2)
        body.tag_config("codex_progress_bar", foreground=COLORS["accent_line"], background=COLORS["bg_card_3"], font=FONTS["mono_small"], lmargin1=22, lmargin2=22, rmargin=24, spacing1=3, spacing3=3)
        body.tag_config("codex_card_line", foreground=COLORS["text_main"], background=COLORS["bg_card_3"], font=FONTS.get("chat_body", FONTS["body"]), lmargin1=34, lmargin2=50, rmargin=24, spacing1=2, spacing2=wrap_line_extra, spacing3=3)
        body.tag_config("codex_card_done", foreground=COLORS["success"], background=COLORS["bg_card_3"], font=FONTS["body_bold"], lmargin1=34, lmargin2=50, rmargin=24, spacing1=2, spacing3=3)
        body.tag_config("codex_card_warn", foreground=COLORS["warning"], background=COLORS["bg_card_3"], font=FONTS["body_bold"], lmargin1=34, lmargin2=50, rmargin=24, spacing1=2, spacing3=3)
        body.tag_config("codex_card_error", foreground=COLORS["danger"], background=COLORS["bg_card_3"], font=FONTS["body_bold"], lmargin1=34, lmargin2=50, rmargin=24, spacing1=2, spacing3=3)
        body.tag_config("chat_message_gap", foreground=COLORS["divider"], spacing1=3, spacing3=8)
        body.tag_config("md_citation", foreground=COLORS["text_weak"], font=FONTS["small"], lmargin1=24, lmargin2=36, spacing1=2, spacing3=2)
        body.tag_config("md_math", foreground=COLORS["accent_line"], background=COLORS["bg_card_3"], font=FONTS["mono"])
        body.tag_config("md_link", foreground=COLORS["accent_line"], underline=True)
        body.tag_config("md_rule", foreground=COLORS["divider"], spacing1=4, spacing3=4)

    def _insert_inline_markdown(self, body: tk.Text, text: str, base_tags: tuple[str, ...]) -> None:
        pos = 0
        for match in self._INLINE_MD_RE.finditer(text):
            if match.start() > pos:
                body.insert("end", text[pos:match.start()], base_tags)
            token = match.group(0)
            if token.startswith("**") and token.endswith("**") and len(token) > 4:
                body.insert("end", token[2:-2], base_tags + ("md_bold",))
            elif token.startswith("~~") and token.endswith("~~") and len(token) > 4:
                body.insert("end", token[2:-2], base_tags + ("md_strike",))
            elif token.startswith("`") and token.endswith("`") and len(token) > 2:
                body.insert("end", token[1:-1], base_tags + ("md_inline_code",))
            elif (token.startswith("*") and token.endswith("*") and len(token) > 2) or (token.startswith("_") and token.endswith("_") and len(token) > 2):
                body.insert("end", token[1:-1], base_tags + ("md_italic",))
            elif (token.startswith("$") and token.endswith("$") and len(token) > 2):
                body.insert("end", token, base_tags + ("md_math",))
            elif re.match(r"^\[\^?\d+\]$", token):
                body.insert("end", token, base_tags + ("md_citation",))
            elif token.startswith("[") and "](" in token and token.endswith(")"):
                label = token[1:token.index("](")].strip() or "链接"
                body.insert("end", label, base_tags + ("md_link",))
            elif token.startswith("http://") or token.startswith("https://") or token.startswith("sandbox:/"):
                clean = token.rstrip(".,;，。；")
                body.insert("end", clean, base_tags + ("md_link",))
                tail = token[len(clean):]
                if tail:
                    body.insert("end", tail, base_tags)
            else:
                body.insert("end", token, base_tags)
            pos = match.end()
        if pos < len(text):
            body.insert("end", text[pos:], base_tags)

    def _normalize_chat_emojis(self, text: str) -> str:
        mapping = {
            ":smile:": "😄", ":happy:": "😊", ":ok:": "👌", ":thumbsup:": "👍", ":+1:": "👍",
            ":fire:": "🔥", ":sparkles:": "✨", ":thinking:": "🤔", ":warning:": "⚠️", ":check:": "✅",
            "[表情:开心]": "😊", "[表情:赞]": "👍", "[表情:收到]": "👌", "[表情:思考]": "🤔", "[表情:火]": "🔥",
        }
        out = text
        for key, value in mapping.items():
            out = out.replace(key, value)
        return out

    def _is_markdown_table_row(self, line: str) -> bool:
        stripped = line.strip()
        if "|" not in stripped:
            return False
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        return len(cells) >= 2 and any(cells)

    def _is_markdown_table_separator(self, line: str) -> bool:
        if not self._is_markdown_table_row(line):
            return False
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        return bool(cells) and all(re.match(r"^:?-{3,}:?$", cell or "") for cell in cells)

    def _is_markdown_table_start(self, lines: list[str], index: int) -> bool:
        return (
            index + 1 < len(lines)
            and self._is_markdown_table_row(lines[index])
            and self._is_markdown_table_separator(lines[index + 1])
        )

    def _render_markdown_table(self, body: tk.Text, table_lines: list[str], base_tags: tuple[str, ...]) -> None:
        rows: list[list[str]] = []
        for line in table_lines:
            if self._is_markdown_table_separator(line):
                continue
            cells = [safe_text(cell.strip(), 80) for cell in line.strip().strip("|").split("|")]
            rows.append(cells)
        if not rows:
            return
        col_count = max(len(row) for row in rows)
        for row in rows:
            row.extend([""] * (col_count - len(row)))
        widths = [min(28, max(4, max(len(row[idx]) for row in rows))) for idx in range(col_count)]
        for idx, row in enumerate(rows):
            line = " │ ".join((row[col][: widths[col]]).ljust(widths[col]) for col in range(col_count))
            tag = "md_table_header" if idx == 0 else "md_table"
            body.insert("end", line + "\n", base_tags + (tag,))
            if idx == 0:
                sep = "─┼─".join("─" * widths[col] for col in range(col_count))
                body.insert("end", sep + "\n", base_tags + ("md_table_separator",))
        body.insert("end", "\n", base_tags)

    def _event_line_tag(self, line: str) -> tuple[str, str] | None:
        stripped = line.strip()
        if re.match(r"^(错误|失败|Error|Failed|Exception|Traceback)[:：]", stripped, re.I):
            return ("✖ ", "md_event_error")
        if re.match(r"^(警告|注意|Warning|审批|确认|QualityGate|质量门)[:：]", stripped, re.I):
            return ("⚠ ", "md_event_warning")
        if re.match(r"^(成功|完成|PASS|OK|通过)[:：]", stripped, re.I):
            return ("✓ ", "md_event_success")
        if re.match(r"^(Run|运行|任务|工具|Tool|Planner|Runtime|Provider|状态|事件|当前|阶段|心跳|审计)[:：]", stripped, re.I):
            return ("▣ ", "md_event")
        return None

    def _is_citation_or_footnote_line(self, line: str) -> bool:
        stripped = line.strip()
        return bool(re.match(r"^(\[\^?\d+\]|来源|引用|参考|References?|Sources?)[:：]", stripped, re.I))

    def _is_codex_progress_card_start(self, line: str) -> bool:
        stripped = line.strip()
        return stripped.startswith("▣ Codex进度｜") or stripped.startswith("◇ Codex进度｜")

    def _is_task_flow_progress_message(self, msg: Any) -> bool:
        role = safe_text(getattr(msg, "role", ""), 32).lower()
        content = safe_chat_text(getattr(msg, "text", ""), 1200)
        meta_time = safe_text(getattr(msg, "time", ""), 40)
        stripped = content.lstrip()
        if role in {"progress", "runtime_progress", "event"}:
            return True
        if "Codex进度" in stripped or stripped.startswith("▣ Codex进度｜") or stripped.startswith("◇ Codex进度｜"):
            return True
        if meta_time == "进度" and any(k in stripped for k in ("长链任务", "任务已", "Planner", "Runtime", "QualityGate")):
            return True
        return False

    def _codex_line_tag(self, stripped: str) -> str:
        lower = stripped.lower()
        if any(word in stripped for word in ("失败", "错误", "阻断", "异常")) or any(word in lower for word in ("failed", "error", "exception", "blocked")):
            return "codex_card_error"
        if any(word in stripped for word in ("审批", "等待", "警告", "注意")) or any(word in lower for word in ("warning", "pending", "approval")):
            return "codex_card_warn"
        if any(word in stripped for word in ("完成", "成功", "通过", "已返回", "已收口")) or any(word in lower for word in ("pass", "ok", "success", "completed")):
            return "codex_card_done"
        return "codex_card_line"

    def _render_codex_progress_card(self, body: tk.Text, card_lines: list[str], base_tags: tuple[str, ...]) -> None:
        if not card_lines:
            return
        title = card_lines[0].strip().replace("◇ Codex进度｜", "").replace("▣ Codex进度｜", "").strip() or "任务进度"
        body.insert("end", f"▣ {title}\n", base_tags + ("codex_card_header",))
        for raw_line in card_lines[1:]:
            stripped = raw_line.strip()
            if not stripped:
                continue
            if stripped.startswith("进度条：") or "█" in stripped or "░" in stripped:
                bar = stripped.replace("进度条：", "").strip()
                body.insert("end", f"{bar}\n", base_tags + ("codex_progress_bar",))
                continue
            if re.match(r"^(状态|Run|当前|工具|下一步)[:：]", stripped):
                body.insert("end", stripped + "\n", base_tags + ("codex_card_meta",))
                continue
            bullet = re.match(r"^[-•*]\s+(.+)$", stripped)
            if bullet:
                tag = self._codex_line_tag(bullet.group(1))
                body.insert("end", "• ", base_tags + (tag,))
                self._insert_inline_markdown(body, bullet.group(1), base_tags + (tag,))
                body.insert("end", "\n", base_tags + (tag,))
                continue
            tag = self._codex_line_tag(stripped)
            self._insert_inline_markdown(body, stripped, base_tags + (tag,))
            body.insert("end", "\n", base_tags + (tag,))
        body.insert("end", "\n", base_tags)

    def _insert_markdown_text(self, body: tk.Text, raw_text: Any, base_tags: tuple[str, ...] = ("body",)) -> None:
        text = self._normalize_chat_emojis(safe_chat_text(raw_text, CHAT_MESSAGE_DISPLAY_LIMIT))
        if not text:
            body.insert("end", "（空响应）\n", base_tags)
            return

        lines = text.split("\n")
        in_code = False
        fence = ""
        idx = 0
        while idx < len(lines):
            line = lines[idx]
            stripped = line.strip()

            if stripped.startswith("```") or stripped.startswith("~~~"):
                marker = stripped[:3]
                if not in_code:
                    in_code = True
                    fence = marker
                    lang = safe_text(stripped[3:].strip(), 30)
                    body.insert("end", f"{lang or 'code'}\n", base_tags + ("md_code_label", "md_code_block"))
                elif marker == fence:
                    in_code = False
                    fence = ""
                    body.insert("end", "\n", base_tags)
                else:
                    body.insert("end", line + "\n", base_tags + ("md_code_block",))
                idx += 1
                continue

            if in_code:
                body.insert("end", line + "\n", base_tags + ("md_code_block",))
                idx += 1
                continue

            if not stripped:
                body.insert("end", "\n", base_tags)
                idx += 1
                continue

            if self._is_codex_progress_card_start(stripped):
                card_lines = [line]
                idx += 1
                while idx < len(lines) and lines[idx].strip():
                    card_lines.append(lines[idx])
                    idx += 1
                if self._show_task_flow_enabled():
                    self._render_codex_progress_card(body, card_lines, base_tags)
                continue

            if self._is_markdown_table_start(lines, idx):
                table_lines = [lines[idx], lines[idx + 1]]
                idx += 2
                while idx < len(lines) and self._is_markdown_table_row(lines[idx]):
                    table_lines.append(lines[idx])
                    idx += 1
                self._render_markdown_table(body, table_lines, base_tags)
                continue

            heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
            if heading:
                level = min(4, len(heading.group(1)))
                body.insert("end", heading.group(2).strip() + "\n", base_tags + (f"md_heading{level}",))
                idx += 1
                continue

            if re.match(r"^[-*_]{3,}$", stripped):
                body.insert("end", "────────────────────────\n", base_tags + ("md_rule",))
                idx += 1
                continue

            event_tag = self._event_line_tag(stripped)
            if event_tag:
                prefix, tag = event_tag
                body.insert("end", prefix, base_tags + (tag,))
                self._insert_inline_markdown(body, stripped, base_tags + (tag,))
                body.insert("end", "\n", base_tags + (tag,))
                idx += 1
                continue

            if self._is_citation_or_footnote_line(stripped):
                body.insert("end", "↳ ", base_tags + ("md_citation",))
                self._insert_inline_markdown(body, stripped, base_tags + ("md_citation",))
                body.insert("end", "\n", base_tags + ("md_citation",))
                idx += 1
                continue

            quote = re.match(r"^>\s?(.*)$", line)
            if quote:
                body.insert("end", "│ ", base_tags + ("md_quote",))
                self._insert_inline_markdown(body, quote.group(1), base_tags + ("md_quote",))
                body.insert("end", "\n", base_tags + ("md_quote",))
                idx += 1
                continue

            task = re.match(r"^(\s*)[-*+]\s+\[([ xX])\]\s+(.+)$", line)
            if task:
                done = task.group(2).lower() == "x"
                icon = "☑ " if done else "☐ "
                tag = "md_task_done" if done else "md_task_pending"
                body.insert("end", icon, base_tags + (tag,))
                self._insert_inline_markdown(body, task.group(3), base_tags + (tag,))
                body.insert("end", "\n", base_tags + (tag,))
                idx += 1
                continue

            bullet = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
            if bullet:
                indent = min(4, len(bullet.group(1).replace("\t", "    ")) // 2)
                body.insert("end", ("  " * indent) + "• ", base_tags + ("md_list",))
                self._insert_inline_markdown(body, bullet.group(2), base_tags + ("md_list",))
                body.insert("end", "\n", base_tags + ("md_list",))
                idx += 1
                continue

            numbered = re.match(r"^(\s*)(\d+)[.)]\s+(.+)$", line)
            if numbered:
                indent = min(4, len(numbered.group(1).replace("\t", "    ")) // 2)
                body.insert("end", ("  " * indent) + f"{numbered.group(2)}. ", base_tags + ("md_list",))
                self._insert_inline_markdown(body, numbered.group(3), base_tags + ("md_list",))
                body.insert("end", "\n", base_tags + ("md_list",))
                idx += 1
                continue

            self._insert_inline_markdown(body, line, base_tags)
            body.insert("end", "\n", base_tags)
            idx += 1

        if in_code:
            body.insert("end", "\n", base_tags)

    def _format_chat_meta_time(self, raw_time: Any) -> str:
        raw = safe_text(raw_time, 32)
        if re.match(r"^\d{1,2}:\d{2}(?::\d{2})?$", raw):
            return raw
        now = time.strftime("%H:%M:%S")
        if raw and raw not in {"当前", "--:--:--"}:
            return f"{now} · {raw}"
        return now

    def _insert_chat_message(self, body: tk.Text, msg: Any, index: int) -> None:
        mark = f"chat_msg_{index}_start"
        try:
            body.mark_set(mark, "end-1c")
        except tk.TclError:
            body.mark_set(mark, "end")
        role = safe_text(getattr(msg, "role", "assistant"), 32).lower()
        is_user = role in {"user", "human"}
        persona_name = safe_text(getattr(self, "persona_name_var", tk.StringVar(value="临渊者")).get(), 32) or "临渊者"
        label = "你" if is_user else safe_text(getattr(msg, "label", persona_name), 32) or persona_name
        if not is_user and label == "临渊者":
            label = persona_name
        time_text = self._format_chat_meta_time(getattr(msg, "time", ""))
        meta_tag = "meta_user" if is_user else "meta_assistant"
        bubble_tag = "bubble_user" if is_user else "bubble_assistant"
        avatar = "你" if is_user else label
        prefix = f"{avatar}  {time_text}".rstrip()
        body.insert("end", prefix + "\n", ("meta", meta_tag))
        display_text = enhance_conversation_readability(getattr(msg, "text", ""), is_assistant=not is_user)
        self._insert_markdown_text(body, display_text, ("body", bubble_tag))
        body.insert("end", "\n", "chat_message_gap")

    def _render_chat_messages_into(self, body: tk.Text, s: RuntimeSnapshot, *, auto_scroll: bool = True) -> None:
        """Render transcript without resetting the viewport to the first line.

        L6.71.7 keeps the L6.71.2 no-jump incremental render path.  New messages are
        appended, and a streaming last-message update only rewrites the last
        message range.  Full rebuild remains a fallback for non-prefix changes.
        """
        try:
            messages = list(getattr(s, "chat_messages", []) or [])
            if not self._show_task_flow_enabled():
                messages = [msg for msg in messages if not self._is_task_flow_progress_message(msg)]
            new_signatures = [self._chat_message_signature(msg) for msg in messages]
            old_signatures = list(getattr(self, "_chat_render_signatures", []) or [])

            body.configure(state="normal")
            self._configure_chat_markdown_tags(body)

            append_from = 0
            full_rebuild = False
            rewrite_last = False

            if not old_signatures:
                full_rebuild = True
            elif len(new_signatures) < len(old_signatures):
                full_rebuild = True
            elif new_signatures[: len(old_signatures)] == old_signatures:
                append_from = len(old_signatures)
            elif len(new_signatures) == len(old_signatures) and len(new_signatures) > 0 and new_signatures[:-1] == old_signatures[:-1]:
                rewrite_last = True
                append_from = len(new_signatures) - 1
            else:
                full_rebuild = True

            if full_rebuild:
                self._chat_full_rebuild_count += 1
                body.delete("1.0", "end")
                append_from = 0
            elif rewrite_last:
                self._chat_rewrite_last_count += 1
                mark = f"chat_msg_{append_from}_start"
                if mark in body.mark_names():
                    body.delete(mark, "end")
                else:
                    body.delete("1.0", "end")
                    append_from = 0

            appended = 0
            for idx, msg in enumerate(messages[append_from:], start=append_from):
                self._insert_chat_message(body, msg, idx)
                appended += 1
            self._chat_append_count += appended

            self._chat_render_signatures = new_signatures
            body.configure(state="disabled")
            try:
                self._persist_current_chat_history(s)
            except Exception as exc:
                self._record_ui_warning("chat_history_autosave", exc, 120)
            if auto_scroll:
                self._force_chat_scroll_to_end(body)
                self._hide_new_message_button()
            elif appended or rewrite_last:
                self._show_new_message_button()
        except tk.TclError as exc:
            self._record_ui_warning("last_chat_render_error", exc, 120)

    def _force_chat_scroll_to_end(self, body: tk.Text | None = None) -> None:
        widget = body or getattr(self, "_chat_body_widget", None)
        if widget is None:
            return
        def pin() -> None:
            try:
                if widget.winfo_exists():
                    widget.see("end")
                    widget.yview_moveto(1.0)
            except tk.TclError as exc:
                self._record_ui_warning("last_chat_scroll_error", exc, 120)
        pin()
        for delay in (0, 25, 80, 180):
            try:
                widget.after(delay, pin)
            except tk.TclError as exc:
                self._record_ui_warning("last_chat_scroll_schedule_error", exc, 120)

    def _stream_activity_label(self, s: RuntimeSnapshot) -> str:
        state = safe_text(getattr(s, "stream_state", "idle"), 40).lower()
        stage = safe_text(getattr(s, "current_stage", ""), 80)
        if state in {"thinking", "submitted", "queued"}:
            return "正在思考"
        if state == "streaming":
            if "输出" in stage or getattr(s, "pending_delta_chars", 0):
                return "正在输出"
            return "正在思考"
        if state == "reconnecting":
            return "断线续接中"
        return ""

    def _stream_status_line(self, s: RuntimeSnapshot, *, finished: bool = False) -> str:
        state = safe_text(getattr(s, "stream_state", "unknown"), 40).lower()
        visible = getattr(s, "visible_message_count", len(getattr(s, "chat_messages", []) or []))
        hidden = getattr(s, "hidden_message_count", 0)
        seq = getattr(s, "last_event_seq", 0)
        reconnect = getattr(s, "reconnect_attempts", 0)
        if finished or state == "completed":
            return f"流式状态：完成 · seq={seq} · visible={visible} · hidden={hidden}"
        if state == "thinking":
            return f"流式状态：思考中 · seq={seq} · reconnect={reconnect} · visible={visible}"
        if state == "streaming":
            return f"流式状态：输出中 · seq={seq} · visible={visible} · hidden={hidden}"
        if state == "reconnecting":
            return f"流式状态：续接中 · reconnect={reconnect} · seq={seq}"
        if state in {"error", "interrupted"}:
            return f"流式状态：{state} · seq={seq} · reconnect={reconnect}"
        return f"流式状态：{state or 'idle'} · seq={seq} · visible={visible}"

    def _cancel_live_stream_indicator(self) -> None:
        after_id = getattr(self, "_live_stream_after_id", None)
        self._live_stream_after_id = None
        self._live_stream_active = False
        if after_id:
            try:
                self.after_cancel(after_id)
            except tk.TclError as exc:
                self._record_ui_warning("last_live_indicator_cancel_error", exc, 120)

    def _start_live_stream_indicator(self, label: str) -> None:
        label = safe_text(label, 40)
        if not label:
            return
        if self._live_stream_base != label:
            self._live_stream_tick = 0
            self._live_stream_base = label
        self._live_stream_active = True
        if label not in self._live_indicator_history:
            self._live_indicator_history.append(label)
            self._live_indicator_history = self._live_indicator_history[-20:]
        self._tick_live_stream_indicator()

    def _tick_live_stream_indicator(self) -> None:
        if not getattr(self, "_live_stream_active", False):
            return
        self._live_stream_tick = (self._live_stream_tick + 1) % 4
        dots = "" if self._live_stream_tick == 0 else "·" * self._live_stream_tick
        self.live_stream_var.set((self._live_stream_base + " " + dots).rstrip())
        if self.winfo_exists():
            try:
                if getattr(self, "_live_stream_after_id", None):
                    self.after_cancel(self._live_stream_after_id)
                self._live_stream_after_id = self.after(360, self._tick_live_stream_indicator)
            except tk.TclError as exc:
                self._record_ui_warning("last_live_indicator_schedule_error", exc, 120)

    def _finish_live_stream_indicator(self, label: str = "已完成") -> None:
        self._cancel_live_stream_indicator()
        self.live_stream_var.set(safe_text(label, 40))
        def clear() -> None:
            try:
                if not getattr(self, "_live_stream_active", False):
                    self.live_stream_var.set("")
            except tk.TclError as exc:
                self._record_ui_warning("last_live_indicator_clear_error", exc, 120)
        try:
            self.after(900, clear)
        except tk.TclError as exc:
            self._record_ui_warning("last_live_indicator_clear_schedule_error", exc, 120)

    def _sync_live_stream_indicator(self, s: RuntimeSnapshot, *, finished: bool = False) -> None:
        state = safe_text(getattr(s, "stream_state", "idle"), 40).lower()
        if finished or state == "completed":
            self._finish_live_stream_indicator("已完成")
            return
        if state in {"error", "interrupted"}:
            self._finish_live_stream_indicator("已停止")
            return
        label = self._stream_activity_label(s)
        if label:
            self._start_live_stream_indicator(label)
        elif state in {"idle", "ready"}:
            self._cancel_live_stream_indicator()
            self.live_stream_var.set("")

    def _render_live_chat_transcript(self, s: RuntimeSnapshot) -> bool:
        body = getattr(self, "_chat_body_widget", None)
        if body is None:
            return False
        try:
            if not body.winfo_exists():
                return False
        except tk.TclError:
            return False
        self._render_chat_messages_into(body, s, auto_scroll=self._chat_should_auto_scroll(body))
        self._maybe_show_permission_popup(s)
        return True

    def _populate_task_snapshot(self, card: Card, s: RuntimeSnapshot, compact: bool = True) -> None:
        snap = s.task_snapshot
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        head = tk.Frame(body, bg=COLORS["bg_card"])
        head.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        head.grid_columnconfigure(0, weight=1)
        tk.Label(head, text=safe_text(snap.current_stage, 42), bg=COLORS["bg_card"], fg=COLORS["accent"], font=FONTS["body_bold"], wraplength=260, justify="left").grid(row=0, column=0, sticky="w")
        StatusPill(head, "待确认" if snap.waiting_user_confirmation else s.current_task_status, "PENDING" if snap.waiting_user_confirmation else s.current_task_status, small=True).grid(row=0, column=1, sticky="e")

        pb_row = tk.Frame(body, bg=COLORS["bg_card"])
        pb_row.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        pb_row.grid_columnconfigure(0, weight=1)
        ttk.Progressbar(pb_row, style="LZ.Horizontal.TProgressbar", maximum=100, value=s.progress_percent).grid(row=0, column=0, sticky="ew")
        tk.Label(pb_row, text=f"{s.progress_percent}%", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small_bold"]).grid(row=0, column=1, sticky="e", padx=(10, 0))

        rows = [
            ("当前步骤", snap.current_step),
            ("预算", snap.budget_state),
            ("工具", snap.tool_state),
            ("快照", snap.snapshot_ref),
        ]
        for idx, (label, value) in enumerate(rows, start=2):
            LabeledValue(body, label, safe_text(value, 48)).grid(row=idx, column=0, sticky="ew", pady=3)

        if snap.completed_steps and not compact:
            make_hint(body, "已完成：" + "；".join(snap.completed_steps[:5]), bg=COLORS["bg_card"], wraplength=300).grid(row=6, column=0, sticky="ew", pady=(8, 0))
        if snap.failed_steps:
            make_hint(body, "异常：" + "；".join(snap.failed_steps[:3]), bg=COLORS["bg_card"], wraplength=300).grid(row=7, column=0, sticky="ew", pady=(6, 0))

        action_row = tk.Frame(body, bg=COLORS["bg_card"])
        action_row.grid(row=8, column=0, sticky="w", pady=(10, 0))
        pending_ticket_id = ""
        for ticket in list(getattr(s, "pending_confirmations", []) or []):
            pending_ticket_id = safe_text(ticket.get("ticket_id", ""), 80)
            if pending_ticket_id:
                break
        if not pending_ticket_id:
            for guard in list(getattr(s, "action_guard_cards", []) or []):
                if bool(getattr(guard, "requires_user_confirmation", False)):
                    pending_ticket_id = safe_text(getattr(guard, "ticket_id", ""), 80)
                    if pending_ticket_id:
                        break
        if snap.waiting_user_confirmation and pending_ticket_id:
            tk.Button(action_row, text="允许请求", command=lambda tid=pending_ticket_id: self._submit_action_guard_decision(tid, "approve"), bg=COLORS["success"], fg="#FFFFFF", relief="flat", padx=10, pady=5).pack(side="left", padx=(0, 6))
            tk.Button(action_row, text="拒绝", command=lambda tid=pending_ticket_id: self._submit_action_guard_decision(tid, "reject"), bg=COLORS["danger"], fg="#FFFFFF", relief="flat", padx=10, pady=5).pack(side="left", padx=(0, 6))
        elif snap.waiting_user_confirmation:
            tk.Button(action_row, text="查看确认", command=lambda: self.show_page("execution"), bg=COLORS["warning"], fg="#FFFFFF", relief="flat", padx=10, pady=5).pack(side="left", padx=(0, 6))
        tk.Button(action_row, text="执行详情", command=lambda: self.show_page("execution"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).pack(side="left")

    def _populate_conversation_guide(self, card: Card, s: RuntimeSnapshot) -> None:
        guide = s.conversation_guide
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        make_hint(body, safe_text(guide.intent_summary, 120), bg=COLORS["bg_card"], wraplength=300).grid(row=0, column=0, sticky="ew", pady=(0, 8))
        actions = guide.recommended_actions[:3] or ["继续下一步"]
        for idx, action in enumerate(actions, start=1):
            tk.Button(
                body,
                text=f"• {safe_text(action, 64)}",
                command=lambda text=action: self._insert_guided_prompt(text),
                bg=COLORS["bg_card_2"],
                fg=COLORS["text_main"],
                relief="flat",
                anchor="w",
                padx=8,
                pady=4,
            ).grid(row=idx, column=0, sticky="ew", pady=2)
        questions = guide.suggested_questions[:2]
        if questions:
            make_hint(body, "建议问法：" + " / ".join(questions), bg=COLORS["bg_card"], wraplength=300).grid(row=4, column=0, sticky="ew", pady=(8, 0))
        if guide.missing_information:
            make_hint(body, "缺口：" + "；".join(guide.missing_information[:2]), bg=COLORS["bg_card"], wraplength=300).grid(row=5, column=0, sticky="ew", pady=(8, 0))
        make_hint(body, f"风险：{guide.risk_hint}；{guide.continue_hint}", bg=COLORS["bg_card"], wraplength=300).grid(row=6, column=0, sticky="ew", pady=(8, 0))

    def _populate_home_task_status(self, card: Card, s: RuntimeSnapshot) -> None:
        """Minimal homepage task summary.

        STEP10B intentionally keeps this card short. The homepage answers:
        now doing what, how far, can continue or not. Plan IDs and full steps
        belong to the execution page.
        """
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)

        head = tk.Frame(body, bg=COLORS["bg_card"])
        head.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        head.grid_columnconfigure(0, weight=1)
        tk.Label(head, text="任务状态", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=0, column=0, sticky="w")
        StatusPill(head, s.current_task_status, s.current_task_status, small=True).grid(row=0, column=1, sticky="e")

        tk.Label(body, text=s.current_stage, bg=COLORS["bg_card"], fg=COLORS["accent"], font=FONTS["page_title"]).grid(row=1, column=0, sticky="w", pady=(0, 8))
        pb_row = tk.Frame(body, bg=COLORS["bg_card"])
        pb_row.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        pb_row.grid_columnconfigure(0, weight=1)
        pb = ttk.Progressbar(pb_row, style="LZ.Horizontal.TProgressbar", maximum=100, value=s.progress_percent)
        pb.grid(row=0, column=0, sticky="ew")
        tk.Label(pb_row, text=f"{s.progress_percent}%", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small_bold"]).grid(row=0, column=1, sticky="e", padx=(10, 0))

        next_step = next((step.name for step in s.execution_steps if step.status in {"running", "queued", "confirmation_required"}), s.execution_stage)
        LabeledValue(body, "下一步", safe_text(next_step, 40)).grid(row=3, column=0, sticky="ew", pady=(2, 8))
        tk.Button(body, text="执行详情", command=lambda: self.show_page("execution"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=4, column=0, sticky="w")

    def _populate_task_card(self, card: Card, s: RuntimeSnapshot) -> None:
        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        inner.grid_columnconfigure(0, weight=1)
        StatusPill(inner, s.current_task_status, s.current_task_status).grid(row=0, column=0, sticky="w", pady=(0, 10))
        pb = ttk.Progressbar(inner, style="LZ.Horizontal.TProgressbar", maximum=100, value=s.progress_percent)
        pb.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        tk.Label(inner, text=f"{s.progress_percent}%", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=1, column=1, sticky="e", padx=(8, 0))
        for row, (label, value) in enumerate([("计划 ID", s.plan_id), ("当前阶段", s.current_stage), ("预计完成", s.eta)], start=2):
            LabeledValue(inner, label, value).grid(row=row, column=0, columnspan=2, sticky="ew", pady=3)

    def _populate_summary_card(self, card: Card, s: RuntimeSnapshot) -> None:
        metrics = [
            ("✓", "成功", s.success_count, COLORS["success"]),
            ("!", "阻塞", s.blocked_count, COLORS["danger"]),
            ("?", "待确认", s.pending_confirmation_count, COLORS["warning"]),
        ]
        for idx, (icon, label, value, color) in enumerate(metrics, start=1):
            MetricRow(card, icon, label, value, color).grid(
                row=idx, column=0, sticky="ew", padx=14, pady=(8 if idx == 1 else 6, 0)
            )
        make_hint(card, "执行摘要不在首页展示；完整执行计数进入“执行”页。", bg=COLORS["bg_card"], wraplength=340).grid(
            row=len(metrics) + 1, column=0, sticky="ew", padx=14, pady=(12, 14)
        )

    def _build_execution_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        header = self._page_header(root, "执行", "完整执行链摘要、质量门、恢复续接与确认票据。仍然只展示脱敏字段。")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(0, weight=1)

        timeline = Card(body, "执行链 Timeline")
        timeline.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        self._populate_timeline_table(timeline, s.execution_steps)

        side = tk.Frame(body, bg=COLORS["bg_root"], width=360)
        side.grid(row=0, column=1, sticky="nsew")
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)

        guard = Card(side, "行动守卫卡")
        guard.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self._populate_action_guard(guard, s)

        quality = Card(side, "质量门详情")
        quality.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        self._populate_quality(quality, s, compact=False)

        audit = Card(side, "审计只读卡")
        audit.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        self._populate_audit_readonly_cards(audit, s)

        rollback = Card(side, "回滚只读卡")
        rollback.grid(row=3, column=0, sticky="ew", pady=(0, 16))
        self._populate_rollback_readonly_cards(rollback, s)

        confirmations = Card(side, "确认请求")
        confirmations.grid(row=4, column=0, sticky="ew")
        self._populate_confirmations(confirmations, s)

    def _populate_timeline_table(self, card: Card, steps: Iterable[StepSummary]) -> None:
        rows = list(steps)
        table = tk.Frame(card, bg=COLORS["bg_card"])
        table.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 14))
        headers = ["#", "tool_name", "状态", "risk_level", "audit_ref", "output_summary"]
        widths = [4, 20, 14, 10, 16, 38]
        for col, (header, width) in enumerate(zip(headers, widths)):
            table.grid_columnconfigure(col, weight=1 if col in (1, 5) else 0)
            tk.Label(table, text=header, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], width=width, anchor="w", padx=6, pady=6).grid(row=0, column=col, sticky="ew", padx=(0, 1), pady=(0, 1))
        if not rows:
            make_hint(table, "暂无执行链摘要。", bg=COLORS["bg_card"]).grid(row=1, column=0, columnspan=len(headers), sticky="w", pady=12)
            return
        for r, step in enumerate(rows, start=1):
            values = [str(r), step.name, self._status_cn(step.status), step.risk_level, step.audit_ref, step.output_summary]
            for c, value in enumerate(values):
                color = STATUS_COLORS.get(step.status, COLORS["text_main"]) if c == 2 else COLORS["text_main"]
                tk.Label(table, text=safe_text(value, 120), bg=COLORS["bg_card"], fg=color, font=FONTS["small"], anchor="w", padx=6, pady=6, wraplength=260 if c == 5 else 140).grid(row=r, column=c, sticky="ew", padx=(0, 1), pady=(0, 1))

    def _populate_action_guard(self, card: Card, s: RuntimeSnapshot) -> None:
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        cards = list(getattr(s, "action_guard_cards", []) or [])
        if not cards:
            make_hint(body, "暂无 QualityGate 行动守卫卡。前端保持只读渲染，不自行放行。", bg=COLORS["bg_card"]).grid(row=0, column=0, sticky="ew")
            return
        for idx, guard in enumerate(cards[:2]):
            base = idx * 8
            title = safe_text(getattr(guard, "title", "QualityGate 行动守卫"), 120)
            risk = safe_text(getattr(guard, "risk_level", "A0"), 16)
            decision = safe_text(getattr(guard, "decision", "allowed"), 64)
            ticket_id = safe_text(getattr(guard, "ticket_id", ""), 80)
            tk.Label(body, text=f"{risk} · {decision}", bg=COLORS["bg_card"], fg=COLORS["warning"] if risk in {"A4", "A5"} else COLORS["accent"], font=FONTS["small_bold"]).grid(row=base, column=0, sticky="w")
            tk.Label(body, text=title, bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["body"], wraplength=300, justify="left").grid(row=base + 1, column=0, sticky="w", pady=(2, 4))
            summary = safe_text(getattr(guard, "action_summary", "无动作摘要"), 220)
            scope = safe_text(getattr(guard, "impact_scope", "无影响范围摘要"), 220)
            make_hint(body, f"动作：{summary}\n影响：{scope}", bg=COLORS["bg_card"], wraplength=300).grid(row=base + 2, column=0, sticky="ew", pady=(0, 6))
            steps = list(getattr(guard, "plan_steps", []) or [])[:3]
            if steps:
                make_hint(body, "步骤：" + "；".join(safe_text(item, 80) for item in steps), bg=COLORS["bg_card"], wraplength=300).grid(row=base + 3, column=0, sticky="ew", pady=(0, 6))
            refs = f"ticket={ticket_id or '无'} · audit={safe_text(getattr(guard, 'audit_ref', ''), 50) or '无'} · rollback={safe_text(getattr(guard, 'rollback_ref', ''), 50) or '无'}"
            tk.Label(body, text=refs, bg=COLORS["bg_card"], fg=COLORS["text_weak"], font=FONTS["small"], wraplength=300, justify="left").grid(row=base + 4, column=0, sticky="w", pady=(0, 6))
            btns = tk.Frame(body, bg=COLORS["bg_card"])
            btns.grid(row=base + 5, column=0, sticky="ew", pady=(0, 8))
            requires = bool(getattr(guard, "requires_user_confirmation", False))
            status = safe_text(getattr(guard, "status", "display_only"), 80)
            if not requires:
                tk.Label(btns, text="只读展示：无需用户确认", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(side="left")
            elif status.startswith("runtime_") or status.startswith("frontend_"):
                tk.Label(btns, text=f"已提交请求：{status}", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(side="left")
            else:
                tk.Button(btns, text="允许请求", command=lambda tid=ticket_id: self._submit_action_guard_decision(tid, "approve"), bg=COLORS["success"], fg="#FFFFFF", relief="flat", padx=10, pady=4).pack(side="left", padx=(0, 6))
                tk.Button(btns, text="拒绝请求", command=lambda tid=ticket_id: self._submit_action_guard_decision(tid, "reject"), bg=COLORS["danger"], fg="#FFFFFF", relief="flat", padx=10, pady=4).pack(side="left", padx=(0, 6))
                tk.Button(btns, text="请求修改", command=lambda tid=ticket_id: self._submit_action_guard_decision(tid, "request_changes"), bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=10, pady=4).pack(side="left")

    def _populate_audit_readonly_cards(self, card: Card, s: RuntimeSnapshot) -> None:
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        cards = list(getattr(s, "audit_readonly_cards", []) or [])
        if not cards:
            LabeledValue(body, "审计数量", str(s.audit_count)).grid(row=0, column=0, sticky="ew", pady=4)
            LabeledValue(body, "证据引用", s.evidence_ref).grid(row=1, column=0, sticky="ew", pady=4)
            make_hint(body, "暂无审计只读卡；前端不会写审计。", bg=COLORS["bg_card"]).grid(row=2, column=0, sticky="ew", pady=(8, 0))
            return
        for idx, audit in enumerate(cards[-3:]):
            LabeledValue(body, f"audit[{idx + 1}]", safe_text(getattr(audit, "audit_id", ""), 80) or "无").grid(row=idx * 2, column=0, sticky="ew", pady=3)
            make_hint(body, safe_text(getattr(audit, "summary", "审计事件已记录"), 220), bg=COLORS["bg_card"], wraplength=300).grid(row=idx * 2 + 1, column=0, sticky="ew", pady=(0, 6))

    def _populate_rollback_readonly_cards(self, card: Card, s: RuntimeSnapshot) -> None:
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        cards = list(getattr(s, "rollback_readonly_cards", []) or [])
        if not cards:
            make_hint(body, "暂无回滚票据。即使存在票据，前端也只能展示，不应用回滚。", bg=COLORS["bg_card"], wraplength=300).grid(row=0, column=0, sticky="ew")
            return
        for idx, rb in enumerate(cards[-2:]):
            LabeledValue(body, f"rollback[{idx + 1}]", safe_text(getattr(rb, "ticket_id", ""), 80) or "无").grid(row=idx * 3, column=0, sticky="ew", pady=3)
            LabeledValue(body, "状态", safe_text(getattr(rb, "status", "available"), 80)).grid(row=idx * 3 + 1, column=0, sticky="ew", pady=3)
            make_hint(body, safe_text(getattr(rb, "summary", "回滚票据只读展示"), 220), bg=COLORS["bg_card"], wraplength=300).grid(row=idx * 3 + 2, column=0, sticky="ew", pady=(0, 8))

    def _populate_recovery(self, card: Card, s: RuntimeSnapshot) -> None:
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        items = [
            ("ticket_id", s.recovery_ticket_id or "无"),
            ("failure_count", str(s.recovery_failure_count)),
            ("resume_plan_count", str(s.recovery_resume_plan_count)),
            ("requires_human_confirmation", "是" if s.recovery_requires_human_confirmation else "否"),
        ]
        for idx, (label, value) in enumerate(items):
            LabeledValue(body, label, value).grid(row=idx, column=0, sticky="ew", pady=4)
        actions = "；".join(s.recovery_next_actions) if s.recovery_next_actions else "暂无下一步恢复动作"
        make_hint(body, safe_text(actions, 220)).grid(row=len(items), column=0, sticky="ew", pady=(10, 0))
        tk.Button(body, text="查看恢复动作", command=self._show_recovery_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=len(items) + 1, column=0, sticky="w", pady=(10, 0))

    def _populate_confirmations(self, card: Card, s: RuntimeSnapshot) -> None:
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        if not s.pending_confirmations:
            make_hint(body, "暂无待确认票据。", bg=COLORS["bg_card"]).grid(row=0, column=0, sticky="w")
            return
        for idx, ticket in enumerate(s.pending_confirmations[:3]):
            ticket_id = safe_text(ticket.get("ticket_id", ""), 80)
            title = safe_text(ticket.get("title", "待确认票据"), 120)
            risk = safe_text(ticket.get("risk_level", "A4"), 16)
            tk.Label(body, text=f"{ticket_id} · {risk}", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=idx * 3, column=0, sticky="w")
            tk.Label(body, text=title, bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["body"], wraplength=300, justify="left").grid(row=idx * 3 + 1, column=0, sticky="w", pady=(2, 6))
            btns = tk.Frame(body, bg=COLORS["bg_card"])
            btns.grid(row=idx * 3 + 2, column=0, sticky="ew", pady=(0, 8))
            decision = safe_text(ticket.get("frontend_decision", ""), 32)
            if decision:
                tk.Label(btns, text=f"已记录：{decision}（前端记录）", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(side="left")
            else:
                tk.Button(btns, text="允许请求", command=lambda tid=ticket_id: self._submit_action_guard_decision(tid, "approve"), bg=COLORS["success"], fg="#FFFFFF", relief="flat", padx=12, pady=4).pack(side="left", padx=(0, 8))
                tk.Button(btns, text="拒绝请求", command=lambda tid=ticket_id: self._submit_action_guard_decision(tid, "reject"), bg=COLORS["danger"], fg="#FFFFFF", relief="flat", padx=12, pady=4).pack(side="left")
