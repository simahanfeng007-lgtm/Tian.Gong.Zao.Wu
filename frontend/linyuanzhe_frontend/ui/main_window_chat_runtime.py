from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Dict, Iterable, List

from linyuanzhe_frontend.contracts.product_identity import PRODUCT_IDENTITY
from linyuanzhe_frontend.contracts.model_settings import DEFAULT_MODEL_CATALOG, filter_model_catalog, sanitize_runtime_settings
from linyuanzhe_frontend.contracts.provider_settings import provider_readiness_from_public_projection
from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot, StepSummary, digest_text, safe_chat_text, safe_text
from linyuanzhe_frontend.version_info import PROVIDER_CONFIG_SCHEMA_VERSION
from .theme import COLORS, FONTS, STATUS_COLORS, THEME_PROFILES
from .widgets import Card, Chip, MetricRow, StepItem, LabeledValue, StatusPill, make_button, make_hint, make_readonly_banner, make_section_title


class ChatRuntimeMixin:
    def _build_chat_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        """Homepage: chat-first desktop workspace.

        STEP31Q keeps the main conversation dominant and makes Provider readiness explicit. Runtime details
        move into one collapsible 会话信息 panel so the homepage no longer reads as
        an operations dashboard.
        """
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=0)
        root.grid_rowconfigure(0, weight=1)

        main = tk.Frame(root, bg=COLORS["bg_root"])
        main.grid(row=0, column=0, sticky="nsew", padx=(DIMENS["page_pad"], 6), pady=DIMENS["page_pad"])
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)

        side_width = DIMENS["right_col_w"] if self.session_info_expanded else 108
        side = tk.Frame(root, bg=COLORS["bg_root"], width=side_width)
        side.grid(row=0, column=1, sticky="ns", padx=(6, DIMENS["page_pad"]), pady=DIMENS["page_pad"])
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)
        side.grid_rowconfigure(0, weight=1)

        chat_card = Card(main, "会话")
        chat_card.grid(row=0, column=0, sticky="nsew")
        chat_card.grid_columnconfigure(0, weight=1)
        chat_card.grid_rowconfigure(1, weight=1)
        self._populate_chat_card(chat_card, s)

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
            return "Mock 锁定"
        if readiness.get("readiness") == "missing_credentials":
            return "Mock · 缺 Provider"
        if readiness.get("readiness") == "error":
            return "Provider 异常"
        mode = safe_text(getattr(s, "provider_config_state", "") or getattr(s, "source_kind", ""), 28)
        if "mock" in mode.lower() or "mock" in safe_text(getattr(s, "connection_status", ""), 80).lower():
            return "Mock 模式"
        return safe_text(getattr(s, "runtime_status", "就绪"), 28)

    def _home_continue_hint(self, s: RuntimeSnapshot) -> str:
        readiness = self._provider_readiness_public(self._provider_public_from_snapshot(s))
        if bool(getattr(s.task_snapshot, "waiting_user_confirmation", False)):
            return "当前等待确认。打开质量门详情后再决定允许或拒绝。"
        if not bool(getattr(s, "quality_allow_continue", True)):
            return "质量门显示不可继续。请查看摘要后处理阻断原因。"
        if readiness.get("readiness") != "ready":
            return safe_text(readiness.get("message", "当前仍是 Mock / 本地演示模式；真实模型在设置页填写 Provider 后启用。"), 220)
        return "Provider 就绪，可继续输入任务。详细执行链与审计已下沉，不占用首页。"

    def _populate_chat_card(self, card: Card, s: RuntimeSnapshot) -> None:
        body_wrap = tk.Frame(card, bg=COLORS["bg_card"])
        body_wrap.grid(row=1, column=0, sticky="nsew", padx=14, pady=(4, 10))
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
            padx=4,
            pady=4,
        )
        body.grid(row=0, column=0, sticky="nsew")
        scrollbar = tk.Scrollbar(body_wrap, command=body.yview, bg=COLORS["bg_card"], troughcolor=COLORS["bg_card"])
        scrollbar.grid(row=0, column=1, sticky="ns")
        body.configure(yscrollcommand=scrollbar.set)
        self._chat_body_widget = body
        self._chat_render_signatures = []
        self._render_chat_messages_into(body, s, auto_scroll=True)

        input_shell = tk.Frame(card, bg=COLORS["bg_card"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
        input_shell.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        input_shell.grid_columnconfigure(1, weight=1)

        action_col = tk.Frame(input_shell, bg=COLORS["bg_card"])
        action_col.grid(row=0, column=0, sticky="ns", padx=(10, 8), pady=10)
        tk.Button(action_col, text="附件", command=self._request_file_transfer_from_dialog, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).pack(side="left")

        input_area = tk.Frame(input_shell, bg=COLORS["bg_input"])
        input_area.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=10)
        input_area.grid_columnconfigure(0, weight=1)
        self.input_placeholder_label = tk.Label(
            input_area,
            text="输入消息，Enter 发送，Shift+Enter 换行",
            bg=COLORS["bg_input"],
            fg=COLORS["text_weak"],
            font=FONTS["small"],
        )
        self.input_placeholder_label.grid(row=0, column=0, sticky="w", padx=10, pady=(7, 0))
        self.input_text = tk.Text(
            input_area,
            height=3,
            bg=COLORS["bg_input"],
            fg=COLORS["text_main"],
            insertbackground=COLORS["text_main"],
            relief="flat",
            wrap="word",
            font=FONTS["body"],
            padx=10,
            pady=6,
        )
        self.input_text.grid(row=1, column=0, sticky="ew")
        self.input_text.bind("<Return>", self._send_message_from_event)
        self.input_text.bind("<Shift-Return>", self._insert_newline_from_event)
        self.input_text.bind("<Key>", self._hide_input_placeholder, add="+")
        self.input_text.bind("<FocusIn>", self._sync_input_placeholder, add="+")
        self.input_text.bind("<FocusOut>", self._sync_input_placeholder, add="+")
        self.input_text.bind("<<Modified>>", self._sync_input_placeholder, add="+")
        self._sync_input_placeholder()

        send_col = tk.Frame(input_shell, bg=COLORS["bg_card"])
        send_col.grid(row=0, column=2, sticky="e", padx=(0, 10), pady=10)
        tk.Button(send_col, text="发送", command=self._send_message, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=18, pady=8).pack(side="top", fill="x")
        ctrl_row = tk.Frame(send_col, bg=COLORS["bg_card"])
        ctrl_row.pack(side="top", pady=(6, 0))
        tk.Button(ctrl_row, text="中断", command=self._request_task_interrupt, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=8, pady=4).pack(side="left", padx=(0, 4))
        tk.Button(ctrl_row, text="清屏", command=self._clear_chat_view_frontend_only, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=8, pady=4).pack(side="left", padx=(0, 4))
        tk.Button(ctrl_row, text="停止", command=self._request_task_stop, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=8, pady=4).pack(side="left", padx=(0, 4))
        tk.Button(ctrl_row, text="复位", command=self._request_task_reset, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=8, pady=4).pack(side="left", padx=(0, 4))
        tk.Button(ctrl_row, text="任务", command=lambda: self.show_page("sessions"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=8, pady=4).pack(side="left")
        status_row = tk.Frame(card, bg=COLORS["bg_card"])
        status_row.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))
        status_row.grid_columnconfigure(0, weight=1)
        tk.Label(status_row, textvariable=self.stream_status_var, bg=COLORS["bg_card"], fg=COLORS["text_weak"], font=FONTS["small"]).grid(row=0, column=0, sticky="w")
        tk.Label(status_row, textvariable=self.live_stream_var, bg=COLORS["bg_card"], fg=COLORS["accent_line"], font=FONTS["small_bold"]).grid(row=0, column=1, sticky="e")
        self._sync_live_stream_indicator(self.snapshot, finished=False)

    def _hide_input_placeholder(self, _event: Any | None = None) -> None:
        label = getattr(self, "input_placeholder_label", None)
        if label is not None:
            try:
                label.grid_remove()
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
                label.grid_remove()
            else:
                label.grid()
            try:
                widget.edit_modified(False)
            except tk.TclError as exc:
                self._record_ui_warning("input_placeholder_modified_flag", exc, 120)
        except tk.TclError as exc:
            self._record_ui_warning("input_placeholder_sync", exc, 120)

    def _chat_message_signature(self, msg: Any) -> tuple[str, str, str, str]:
        chat_text = safe_chat_text(getattr(msg, "text", ""), 8000)
        return (
            safe_text(getattr(msg, "role", "assistant"), 32),
            safe_text(getattr(msg, "label", "临渊者"), 32),
            safe_text(getattr(msg, "time", ""), 32),
            digest_text(chat_text, 24),
        )

    def _configure_chat_markdown_tags(self, body: tk.Text) -> None:
        body.tag_config("meta", foreground=COLORS["text_sub"], font=FONTS["small"], spacing3=3)
        body.tag_config("body", foreground=COLORS["text_main"], font=FONTS["body"], spacing1=2, spacing3=3)
        body.tag_config("md_heading1", foreground=COLORS["text_main"], font=FONTS["page_title"], spacing1=8, spacing3=6)
        body.tag_config("md_heading2", foreground=COLORS["text_main"], font=FONTS["section_title"], spacing1=6, spacing3=5)
        body.tag_config("md_heading3", foreground=COLORS["text_main"], font=FONTS["card_title"], spacing1=5, spacing3=4)
        body.tag_config("md_bold", foreground=COLORS["text_main"], font=FONTS["body_bold"])
        body.tag_config("md_inline_code", foreground=COLORS["accent_line"], background=COLORS["bg_card_2"], font=FONTS["mono"])
        body.tag_config("md_code_block", foreground=COLORS["text_main"], background=COLORS["bg_input"], font=FONTS["mono"], lmargin1=14, lmargin2=14, rmargin=14, spacing1=3, spacing3=3)
        body.tag_config("md_code_label", foreground=COLORS["text_weak"], background=COLORS["bg_input"], font=FONTS["small_bold"], lmargin1=14, lmargin2=14, spacing1=4, spacing3=2)
        body.tag_config("md_list", foreground=COLORS["text_main"], font=FONTS["body"], lmargin1=18, lmargin2=34, spacing1=2, spacing3=2)
        body.tag_config("md_quote", foreground=COLORS["text_sub"], font=FONTS["body"], lmargin1=16, lmargin2=28, spacing1=2, spacing3=2)
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
            elif token.startswith("`") and token.endswith("`") and len(token) > 2:
                body.insert("end", token[1:-1], base_tags + ("md_inline_code",))
            elif token.startswith("[") and "](" in token and token.endswith(")"):
                label = token[1:token.index("](")].strip() or "链接"
                body.insert("end", label, base_tags + ("md_link",))
            elif token.startswith("http://") or token.startswith("https://"):
                body.insert("end", token.rstrip(".,;，。；"), base_tags + ("md_link",))
                tail = token[len(token.rstrip(".,;，。；")):]
                if tail:
                    body.insert("end", tail, base_tags)
            else:
                body.insert("end", token, base_tags)
            pos = match.end()
        if pos < len(text):
            body.insert("end", text[pos:], base_tags)

    def _insert_markdown_text(self, body: tk.Text, raw_text: Any) -> None:
        text = safe_chat_text(raw_text, 8000)
        if not text:
            body.insert("end", "（空响应）\n", "body")
            return

        in_code = False
        fence = ""
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                marker = stripped[:3]
                if not in_code:
                    in_code = True
                    fence = marker
                    lang = safe_text(stripped[3:].strip(), 30)
                    body.insert("end", f"{lang or 'code'}\n", ("md_code_label", "md_code_block"))
                elif marker == fence:
                    in_code = False
                    fence = ""
                    body.insert("end", "\n", "body")
                else:
                    body.insert("end", line + "\n", "md_code_block")
                continue

            if in_code:
                body.insert("end", line + "\n", "md_code_block")
                continue

            if not stripped:
                body.insert("end", "\n", "body")
                continue

            heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
            if heading:
                level = len(heading.group(1))
                body.insert("end", heading.group(2).strip() + "\n", f"md_heading{level}")
                continue

            if re.match(r"^[-*_]{3,}$", stripped):
                body.insert("end", "────────────────────────\n", "md_rule")
                continue

            quote = re.match(r"^>\s?(.*)$", line)
            if quote:
                body.insert("end", "│ ", "md_quote")
                self._insert_inline_markdown(body, quote.group(1), ("md_quote",))
                body.insert("end", "\n", "md_quote")
                continue

            bullet = re.match(r"^\s*[-*+]\s+(.+)$", line)
            if bullet:
                body.insert("end", "• ", "md_list")
                self._insert_inline_markdown(body, bullet.group(1), ("md_list",))
                body.insert("end", "\n", "md_list")
                continue

            numbered = re.match(r"^\s*(\d+)[.)]\s+(.+)$", line)
            if numbered:
                body.insert("end", f"{numbered.group(1)}. ", "md_list")
                self._insert_inline_markdown(body, numbered.group(2), ("md_list",))
                body.insert("end", "\n", "md_list")
                continue

            self._insert_inline_markdown(body, line, ("body",))
            body.insert("end", "\n", "body")

        if in_code:
            body.insert("end", "\n", "body")

    def _insert_chat_message(self, body: tk.Text, msg: Any, index: int) -> None:
        mark = f"chat_msg_{index}_start"
        try:
            body.mark_set(mark, "end-1c")
        except tk.TclError:
            body.mark_set(mark, "end")
        prefix = f"{safe_text(getattr(msg, 'label', '临渊者'), 32)}  {safe_text(getattr(msg, 'time', ''), 32)}"
        body.insert("end", prefix + "\n", "meta")
        self._insert_markdown_text(body, getattr(msg, "text", ""))
        body.insert("end", "\n", "body")

    def _render_chat_messages_into(self, body: tk.Text, s: RuntimeSnapshot, *, auto_scroll: bool = True) -> None:
        """Render transcript without resetting the viewport to the first line.

        L6.71.7 keeps the L6.71.2 no-jump incremental render path.  New messages are
        appended, and a streaming last-message update only rewrites the last
        message range.  Full rebuild remains a fallback for non-prefix changes.
        """
        try:
            messages = list(getattr(s, "chat_messages", []) or [])
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
            if auto_scroll:
                self._force_chat_scroll_to_end(body)
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
            return "临渊者正在思考"
        if state == "streaming":
            if "输出" in stage or getattr(s, "pending_delta_chars", 0):
                return "正在输出"
            return "临渊者正在思考"
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
        self._render_chat_messages_into(body, s, auto_scroll=True)
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
                tk.Label(btns, text=f"已记录：{decision}（前端 Mock）", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(side="left")
            else:
                tk.Button(btns, text="允许请求", command=lambda tid=ticket_id: self._submit_action_guard_decision(tid, "approve"), bg=COLORS["success"], fg="#FFFFFF", relief="flat", padx=12, pady=4).pack(side="left", padx=(0, 8))
                tk.Button(btns, text="拒绝请求", command=lambda tid=ticket_id: self._submit_action_guard_decision(tid, "reject"), bg=COLORS["danger"], fg="#FFFFFF", relief="flat", padx=12, pady=4).pack(side="left")
