from __future__ import annotations

import json
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Dict, Iterable, List

from linyuanzhe_frontend.contracts.runtime_client import RuntimeClient
from linyuanzhe_frontend.contracts.product_identity import PRODUCT_IDENTITY
from linyuanzhe_frontend.contracts.model_settings import DEFAULT_MODEL_CATALOG, filter_model_catalog, sanitize_runtime_settings
from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot, StepSummary, digest_text, safe_text
from linyuanzhe_frontend.contracts.streaming_render import RenderScheduler
from .page_specs import ALL_PAGE_DEFINITIONS, DEFAULT_PAGE, PAGE_BY_KEY, PAGE_DEFINITIONS
from .theme import COLORS, DIMENS, FONTS, STATUS_COLORS
from .widgets import Card, Chip, CollapsibleFrame, MetricRow, StepItem, LabeledValue, StatusPill, configure_ttk_style, make_button, make_hint, make_readonly_banner, make_section_title


class LinyuanzheDesktopApp(tk.Tk):
    """FE.01 desktop shell.

    STEP10B locks the corrected homepage into a cleaner desktop presentation:
    chat-first center workspace, fixed input bar, minimal right-side status summary,
    and progressive disclosure for execution details. It still only reads Mock/JSON
    projections and records frontend-only confirmation state.
    """

    def __init__(self, client: RuntimeClient) -> None:
        super().__init__()
        self.client = client
        self.snapshot = client.get_snapshot()
        self.current_page = DEFAULT_PAGE
        self.nav_buttons: Dict[str, tk.Button] = {}
        self.status_labels: Dict[str, tk.Label] = {}
        self.api_provider_var = tk.StringVar(value="deepseek")
        self.api_base_url_var = tk.StringVar(value="")
        self.api_key_var = tk.StringVar(value="")
        self.main_model_var = tk.StringVar(value="deepseek-reasoner")
        self.model_search_var = tk.StringVar(value="")
        self.session_search_var = tk.StringVar(value="")
        self.selected_session_id = ""
        self.settings_status_var = tk.StringVar(value="API 与主模型设置仅在设置页维护；Key/Base URL 写入后仅保留 digest。")
        self.stream_status_var = tk.StringVar(value="流式状态：idle")
        self._sanitized_settings: Dict[str, Any] = {}
        self._stream_worker: threading.Thread | None = None
        self._stream_lock = threading.Lock()
        self._render_scheduler = RenderScheduler(min_interval_ms=45)
        self._pending_stream_snapshot: RuntimeSnapshot | None = None
        self._pending_stream_finished = False
        self._render_after_id: str | None = None
        self.title("临渊者桌面驾驶舱 - FE01 STEP31A / L6.70.1 前后端一体包")
        self.geometry(f"{DIMENS['window_w']}x{DIMENS['window_h']}")
        self.minsize(DIMENS["window_min_w"], DIMENS["window_min_h"])
        self.configure(bg=COLORS["bg_root"])
        configure_ttk_style(self)
        self._build_shell()
        self.bind("<F5>", lambda _event: self._refresh_snapshot_frontend_only())
        self.bind("<Control-r>", lambda _event: self._request_session_resume_active())
        self.bind("<Control-f>", lambda _event: self.show_page("sessions"))
        self.bind("<Control-period>", lambda _event: self._request_task_interrupt())
        self.show_page(DEFAULT_PAGE)

    # ------------------------------------------------------------------ shell
    def _build_shell(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_topbar()
        self._build_sidebar()
        self.content = tk.Frame(self, bg=COLORS["bg_root"])
        self.content.grid(row=1, column=1, sticky="nsew")
        self._build_statusbar()

    def _build_topbar(self) -> None:
        top = tk.Frame(self, bg=COLORS["bg_window"], height=DIMENS["topbar_h"])
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        top.grid_columnconfigure(2, weight=1)

        logo = tk.Label(top, text="◢", fg=COLORS["accent"], bg=COLORS["bg_window"], font=("Segoe UI", 22, "bold"))
        logo.grid(row=0, column=0, padx=(22, 8), pady=10)
        title = tk.Label(top, text="临渊者桌面驾驶舱", fg=COLORS["text_main"], bg=COLORS["bg_window"], font=FONTS["title"])
        title.grid(row=0, column=1, pady=10, sticky="w")
        meta = tk.Frame(top, bg=COLORS["bg_window"])
        meta.grid(row=0, column=2, sticky="w", padx=14)
        tag = Chip(meta, "FE.01 STEP31A · L6.70.1 一体包", "blue")
        tag.pack(side="left")
        tk.Label(
            meta,
            text=f"开发者：{PRODUCT_IDENTITY.unique_developer} · 天使投资人：{PRODUCT_IDENTITY.angel_investor}",
            bg=COLORS["bg_window"],
            fg=COLORS["text_sub"],
            font=FONTS["small"],
        ).pack(side="left", padx=(12, 0))

        actions = [("新建任务", self._new_task_frontend_only), ("任务塔台", lambda: self.show_page("sessions")), ("安装", lambda: self.show_page("installer")), ("设置", lambda: self.show_page("settings"))]
        for idx, (text, command) in enumerate(actions):
            variant = "primary" if idx == 0 else "secondary"
            btn = make_button(top, text, command, variant=variant, padx=14, pady=6)
            btn.grid(row=0, column=3 + idx, padx=(0, 10), pady=10)

    def _build_sidebar(self) -> None:
        side = tk.Frame(self, bg=COLORS["bg_sidebar"], width=DIMENS["sidebar_w"])
        side.grid(row=1, column=0, sticky="nsw")
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)

        brand = tk.Frame(side, bg=COLORS["bg_sidebar_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
        brand.grid(row=0, column=0, sticky="ew", padx=12, pady=(16, 14))
        tk.Label(brand, text="◢", bg=COLORS["bg_sidebar_2"], fg=COLORS["accent_line"], font=("Segoe UI", 18, "bold")).pack(side="left", padx=(12, 6), pady=10)
        tk.Label(brand, text="极夜驾驶舱", bg=COLORS["bg_sidebar_2"], fg=COLORS["text_main"], font=FONTS["small_bold"]).pack(side="left")

        for i, spec in enumerate(ALL_PAGE_DEFINITIONS, start=1):
            btn = tk.Button(
                side,
                text=f"{spec.icon}  {spec.label}",
                anchor="w",
                command=lambda key=spec.key: self.show_page(key),
                relief="flat",
                bd=0,
                padx=18,
                pady=12,
                font=FONTS["body"],
                cursor="hand2",
            )
            btn.grid(row=i, column=0, sticky="ew", padx=12, pady=(0 if i == 1 else 6, 0))
            self.nav_buttons[spec.key] = btn

        boundary = tk.Label(
            side,
            text="FE.01 STEP28\nSession 管理只读",
            bg=COLORS["bg_sidebar"],
            fg=COLORS["text_weak"],
            font=FONTS["small"],
            justify="left",
        )
        boundary.grid(row=len(ALL_PAGE_DEFINITIONS) + 1, column=0, sticky="sw", padx=22, pady=(36, 0))

    def _build_statusbar(self) -> None:
        bar = tk.Frame(self, bg=COLORS["bg_window"], height=DIMENS["statusbar_h"])
        bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)
        status_items = [
            ("runtime_status", "Runtime"),
            ("provider_model", "Provider"),
            ("budget_pool", "Budget"),
            ("budget_used_ratio", "Used"),
            ("gate_status", "Gate"),
            ("audit_id", "Audit"),
            ("memory_mode", "Memory"),
            ("tools_allowed", "Tools"),
            ("latency_ms", "Latency"),
        ]
        for idx, (key, text) in enumerate(status_items):
            cluster = tk.Frame(bar, bg=COLORS["bg_window"])
            cluster.pack(side="left", padx=(14 if idx == 0 else 8, 8), pady=7)
            label = tk.Label(cluster, text=text, bg=COLORS["bg_window"], fg=COLORS["text_sub"], font=FONTS["small"])
            label.pack(side="left")
            self.status_labels[key] = label
            if idx < len(status_items) - 1:
                tk.Frame(bar, bg=COLORS["divider"], width=1, height=16).pack(side="left", pady=10)

    # --------------------------------------------------------------- navigation
    def show_page(self, page_key: str) -> None:
        if page_key not in PAGE_BY_KEY:
            page_key = DEFAULT_PAGE
        self.current_page = page_key
        try:
            self.snapshot = self.client.get_snapshot()
        except Exception as exc:  # defensive UI boundary; do not crash desktop shell
            self.snapshot = RuntimeSnapshot(
                source_kind="client_error",
                runtime_status="读取失败",
                connection_status=f"快照读取失败：{safe_text(exc, 80)}",
                current_task_status="DISCONNECTED",
                progress_percent=0,
                current_stage="前端客户端读取失败",
            )
        self._sync_nav_state()
        self._clear_content()
        if page_key == "chat":
            self._build_chat_page(self.content, self.snapshot)
        elif page_key == "execution":
            self._build_execution_page(self.content, self.snapshot)
        elif page_key == "observability":
            self._build_observability_page(self.content, self.snapshot)
        elif page_key == "sessions":
            self._build_sessions_page(self.content, self.snapshot)
        elif page_key == "files":
            self._build_files_page(self.content, self.snapshot)
        elif page_key == "workspace":
            self._build_workspace_page(self.content, self.snapshot)
        elif page_key == "connectors":
            self._build_connectors_page(self.content, self.snapshot)
        elif page_key == "hooks":
            self._build_hooks_page(self.content, self.snapshot)
        elif page_key == "memory":
            self._build_memory_page(self.content, self.snapshot)
        elif page_key == "iteration":
            self._build_iteration_page(self.content, self.snapshot)
        elif page_key == "four_paths":
            self._build_four_paths_page(self.content, self.snapshot)
        elif page_key == "installer":
            self._build_installer_page(self.content, self.snapshot)
        elif page_key == "settings":
            self._build_settings_page(self.content, self.snapshot)
        self._render_statusbar(self.snapshot)

    def refresh(self) -> None:
        self.show_page(self.current_page)

    def _sync_nav_state(self) -> None:
        for key, btn in self.nav_buttons.items():
            selected = key == self.current_page
            btn.configure(
                bg=COLORS["selected"] if selected else COLORS["bg_sidebar"],
                fg=COLORS["text_main"] if selected else COLORS["text_sub"],
                activebackground=COLORS["selected"],
                activeforeground=COLORS["text_main"],
            )

    def _clear_content(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    # ------------------------------------------------------------------ home
    def _build_chat_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        """STEP10B homepage lock.

        首页冻结为“聊天优先的桌面工作台”：
        - 中央只保留主聊天区和固定输入栏；
        - 右侧只保留当前任务、质量门、审计摘要；
        - 计划 ID、执行计数和完整步骤移入执行页；
        - 首页禁止监控大屏化和卡片堆叠。
        """
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=0)
        root.grid_rowconfigure(0, weight=1)

        main = tk.Frame(root, bg=COLORS["bg_root"])
        main.grid(row=0, column=0, sticky="nsew", padx=DIMENS["page_pad"], pady=DIMENS["page_pad"])
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)

        right = tk.Frame(root, bg=COLORS["bg_root"], width=DIMENS["right_col_w"])
        right.grid(row=0, column=1, sticky="nsew", padx=(0, DIMENS["page_pad"]), pady=DIMENS["page_pad"])
        right.grid_propagate(False)
        right.grid_columnconfigure(0, weight=1)

        chat_card = Card(main, "主聊天区")
        chat_card.grid(row=0, column=0, sticky="nsew")
        chat_card.grid_columnconfigure(0, weight=1)
        chat_card.grid_rowconfigure(1, weight=1)
        self._populate_chat_card(chat_card, s)

        exec_status_card = Card(right, "任务快照")
        exec_status_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self._populate_task_snapshot(exec_status_card, s, compact=True)

        quality_card = Card(right, "质量门")
        quality_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        self._populate_quality(quality_card, s, compact=True)

        audit_card = Card(right, "审计摘要")
        audit_card.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        self._populate_audit(audit_card, s, compact=True)

        guide_card = Card(right, "对话引导")
        guide_card.grid(row=3, column=0, sticky="ew")
        self._populate_conversation_guide(guide_card, s)

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
        # 分离摘要和折叠详情
        import re
        DETAIL_MARKER = re.compile(r"\n--- 执行详情（(.+?)） ---")
        detail_widgets: list[tk.Widget] = []
        for msg in s.chat_messages:
            prefix = f"{msg.label}  {msg.time}"
            body.insert("end", prefix + "\n", "meta")
            m = DETAIL_MARKER.search(msg.text)
            if m:
                parts = DETAIL_MARKER.split(msg.text, maxsplit=1)
                summary = parts[0].strip()
                meta_text = m.group(1)
                detail_content = parts[2].strip() if len(parts) > 2 else ""
                body.insert("end", summary + "\n\n", "body")
                if detail_content:
                    cf = CollapsibleFrame(body_wrap, f"▸ {meta_text}", detail_content, collapsed=True)
                    cf.grid(row=1 + len(detail_widgets), column=0, sticky="ew", padx=4, pady=(0, 6))
                    detail_widgets.append(cf)
            else:
                body.insert("end", msg.text + "\n\n", "body")
        body.tag_config("meta", foreground=COLORS["text_sub"], font=FONTS["small"])
        body.tag_config("body", foreground=COLORS["text_main"], font=FONTS["body"])
        body.configure(state="disabled")

        input_shell = tk.Frame(card, bg=COLORS["bg_card"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
        input_shell.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        input_shell.grid_columnconfigure(1, weight=1)

        action_col = tk.Frame(input_shell, bg=COLORS["bg_card"])
        action_col.grid(row=0, column=0, sticky="ns", padx=(10, 8), pady=10)
        tk.Button(action_col, text="附件", command=self._request_file_transfer_from_dialog, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).pack(side="left", padx=(0, 6))
        tk.Button(action_col, text="任务", command=lambda: self.show_page("sessions"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).pack(side="left", padx=(0, 6))
        tk.Button(action_col, text="计划", command=self._import_plan_frontend_only, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).pack(side="left")

        input_area = tk.Frame(input_shell, bg=COLORS["bg_input"])
        input_area.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=10)
        input_area.grid_columnconfigure(0, weight=1)
        tk.Label(input_area, text="输入消息，Enter 发送，Shift+Enter 换行", bg=COLORS["bg_input"], fg=COLORS["text_weak"], font=FONTS["small"]).grid(row=0, column=0, sticky="w", padx=10, pady=(7, 0))
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

        send_col = tk.Frame(input_shell, bg=COLORS["bg_card"])
        send_col.grid(row=0, column=2, sticky="e", padx=(0, 10), pady=10)
        tk.Button(send_col, text="发送 ↵", command=self._send_message, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=18, pady=8).pack(side="top", fill="x")
        ctrl_row = tk.Frame(send_col, bg=COLORS["bg_card"])
        ctrl_row.pack(side="top", pady=(6, 0))
        tk.Button(ctrl_row, text="中断", command=self._request_task_interrupt, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=8, pady=4).pack(side="left", padx=(0, 4))
        tk.Button(ctrl_row, text="停止", command=self._request_task_stop, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=8, pady=4).pack(side="left", padx=(0, 4))
        tk.Button(ctrl_row, text="复位", command=self._request_task_reset, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=8, pady=4).pack(side="left", padx=(0, 4))
        tk.Button(ctrl_row, text="重连", command=self._request_runtime_reconnect, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=8, pady=4).pack(side="left")
        tk.Label(card, textvariable=self.stream_status_var, bg=COLORS["bg_card"], fg=COLORS["text_weak"], font=FONTS["small"]).grid(row=3, column=0, sticky="w", padx=16, pady=(0, 12))

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
        tk.Button(body, text="执行详情", command=lambda: self.show_page("execution"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=8, column=0, sticky="w", pady=(10, 0))

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

    # --------------------------------------------------------------- execution
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

    # ------------------------------------------------------------- sessions
    def _build_sessions_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(root, "任务 Session 塔台", "L6.67：多任务只读投影、搜索、恢复请求、等待确认、失败归档；不直接恢复工具或应用回滚。").grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(1, weight=1)

        stats = dict(getattr(s, "session_stats", {}) or {})
        metrics = Card(body, "任务指标")
        metrics.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        metric_items = [
            ("总任务", stats.get("total", len(getattr(s, "task_sessions", []) or [])), COLORS["accent"]),
            ("运行", stats.get("running", 0), COLORS["success"]),
            ("待确认", stats.get("waiting_confirmation", 0), COLORS["warning"]),
            ("阻断", stats.get("blocked", 0), COLORS["danger"] if int(stats.get("blocked", 0) or 0) else COLORS["success"]),
            ("可恢复", stats.get("recoverable", 0), COLORS["warning"]),
            ("完成", stats.get("completed", 0), COLORS["text_main"]),
        ]
        metric_body = tk.Frame(metrics, bg=COLORS["bg_card"])
        metric_body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        for col in range(len(metric_items)):
            metric_body.grid_columnconfigure(col, weight=1)
        for idx, (label, value, color) in enumerate(metric_items):
            box = tk.Frame(metric_body, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            box.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 8, 0))
            tk.Label(box, text=str(value), bg=COLORS["bg_card_2"], fg=color, font=FONTS["number"]).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(box, text=label, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(anchor="w", padx=10, pady=(0, 8))
        make_hint(metric_body, f"contract={safe_text(getattr(s, 'session_manager_contract', ''), 100)} · {safe_text(getattr(s, 'session_last_message', ''), 180)}", bg=COLORS["bg_card"], wraplength=980).grid(row=1, column=0, columnspan=len(metric_items), sticky="ew", pady=(10, 0))

        sessions_card = Card(body, "Session 列表")
        sessions_card.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        list_body = tk.Frame(sessions_card, bg=COLORS["bg_card"])
        list_body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 14))
        list_body.grid_columnconfigure(0, weight=1)
        query = safe_text(self.session_search_var.get() or getattr(s, "session_search_query", ""), 120).lower()
        sessions = list(getattr(s, "task_sessions", []) or [])
        if query:
            sessions = [item for item in sessions if query in safe_text(getattr(item, "title", ""), 160).lower() or query in safe_text(getattr(item, "status", ""), 60).lower() or query in safe_text(getattr(item, "current_stage", ""), 160).lower() or any(query in safe_text(tag, 60).lower() for tag in getattr(item, "tags", []) or [])]
        if not sessions:
            make_hint(list_body, "暂无任务投影或当前搜索无命中。", bg=COLORS["bg_card"]).grid(row=0, column=0, sticky="ew", pady=12)
        for idx, item in enumerate(sessions[:40], start=1):
            row = tk.Frame(list_body, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            row.grid(row=idx, column=0, sticky="ew", pady=(0, 8)); row.grid_columnconfigure(0, weight=1)
            title = f"{safe_text(getattr(item, 'title', ''), 100)} · {safe_text(getattr(item, 'status', ''), 40)} · {getattr(item, 'progress_percent', 0)}%"
            tk.Label(row, text=title, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["body_bold"], anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
            msg = f"stage={safe_text(getattr(item, 'current_stage', ''), 100)} · digest={safe_text(getattr(item, 'session_id_digest', ''), 40)} · audit={safe_text(getattr(item, 'audit_id', ''), 40) or '无'}"
            tk.Label(row, text=msg, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=720, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 6))
            buttons = tk.Frame(row, bg=COLORS["bg_card_2"])
            buttons.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 8))
            sid = safe_text(getattr(item, "session_id_digest", ""), 80)
            tk.Button(buttons, text="选中", command=lambda x=sid: self._select_session(x), bg=COLORS["bg_card"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=4).pack(side="left", padx=(0, 6))
            if getattr(item, "recoverable", False):
                tk.Button(buttons, text="请求恢复", command=lambda x=sid: self._request_session_resume(x), bg=COLORS["warning"], fg="#FFFFFF", relief="flat", padx=10, pady=4).pack(side="left", padx=(0, 6))
            tk.Button(buttons, text="详情", command=lambda x=sid: self._show_session_detail(x), bg=COLORS["bg_card"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=4).pack(side="left")

        side = tk.Frame(body, bg=COLORS["bg_root"], width=360)
        side.grid(row=1, column=1, sticky="nsew")
        side.grid_propagate(False)
        search = Card(side, "搜索 / 快捷键")
        search.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        frm = tk.Frame(search, bg=COLORS["bg_card"])
        frm.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14)); frm.grid_columnconfigure(0, weight=1)
        tk.Entry(frm, textvariable=self.session_search_var, bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat", font=FONTS["body"]).grid(row=0, column=0, sticky="ew", ipady=6)
        tk.Button(frm, text="搜索", command=self._request_session_search, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=12, pady=6).grid(row=0, column=1, padx=(8, 0))
        hints = ["F5 刷新", "Ctrl+R 请求恢复", "Ctrl+F 打开任务页", "Ctrl+. 中断当前任务"]
        for i, hint in enumerate(hints, start=1):
            tk.Label(frm, text=f"• {hint}", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=i, column=0, columnspan=2, sticky="w", pady=(8 if i == 1 else 3, 0))

        boundary = Card(side, "任务边界")
        boundary.grid(row=1, column=0, sticky="ew")
        rules = ["只读显示 Runtime Session 投影", "恢复/搜索只提交请求 envelope", "不直接恢复工具或运行命令", "不写长期记忆、审计或回滚", "失败恢复仍由 Runtime / TiangongWangguan 裁决"]
        for idx, rule in enumerate(rules, start=1):
            tk.Label(boundary, text=f"✓ {rule}", bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["small"]).grid(row=idx, column=0, sticky="w", padx=14, pady=(8 if idx == 1 else 4, 0))
        tk.Button(boundary, text="任务详情", command=self._show_session_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=len(rules) + 1, column=0, sticky="w", padx=14, pady=(12, 14))

    # --------------------------------------------------------- observability
    def _build_observability_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(
            root,
            "运行观测台",
            "L6.62 只读 Trace / Observability：展示 Runtime SSE、Agent UI、QualityGate、工具、错误、预算与收口顺序，不产生执行权限。",
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(1, weight=1)

        stats = dict(getattr(s, "trace_stats", {}) or {})
        metrics = Card(body, "Trace 指标")
        metrics.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        self._populate_observability_metrics(metrics, s, stats)

        timeline = Card(body, "Run Trace Timeline")
        timeline.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        self._populate_trace_table(timeline, list(getattr(s, "trace_records", []) or []))

        side = tk.Frame(body, bg=COLORS["bg_root"], width=360)
        side.grid(row=1, column=1, sticky="nsew")
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)

        closeout = Card(side, "SSE 收口")
        closeout.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        LabeledValue(closeout, "assistant_final→run_terminal", "有效" if getattr(s, "trace_terminal_order_valid", True) else "异常", COLORS["success"] if getattr(s, "trace_terminal_order_valid", True) else COLORS["danger"]).grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 4))
        LabeledValue(closeout, "last_seq", str(stats.get("last_seq", getattr(s, "last_event_seq", 0)))).grid(row=2, column=0, sticky="ew", padx=14, pady=4)
        LabeledValue(closeout, "stream_state", safe_text(getattr(s, "stream_state", "idle"), 60)).grid(row=3, column=0, sticky="ew", padx=14, pady=(4, 14))

        runtime = Card(side, "运行状态")
        runtime.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        LabeledValue(runtime, "Runtime", s.runtime_status).grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 4))
        LabeledValue(runtime, "Budget", f"{s.budget_pool} / {s.budget_used_ratio}").grid(row=2, column=0, sticky="ew", padx=14, pady=4)
        LabeledValue(runtime, "Gate", s.gate_status).grid(row=3, column=0, sticky="ew", padx=14, pady=4)
        LabeledValue(runtime, "Latency", f"{s.latency_ms}ms").grid(row=4, column=0, sticky="ew", padx=14, pady=(4, 14))

        boundary = Card(side, "观测边界")
        boundary.grid(row=2, column=0, sticky="ew")
        rules = [
            "只读显示 Runtime PublicProjection / SSE",
            "不裸调 Provider 或工具",
            "不写长期记忆、审计或回滚",
            "run/task 只显示 digest",
            "密钥、路径、端点自动脱敏",
        ]
        for idx, rule in enumerate(rules, start=1):
            tk.Label(boundary, text=f"✓ {rule}", bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["small"]).grid(row=idx, column=0, sticky="w", padx=14, pady=(8 if idx == 1 else 4, 0))
        tk.Button(boundary, text="查看 Trace 详情", command=self._show_observability_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=len(rules) + 1, column=0, sticky="w", padx=14, pady=(12, 14))

    def _populate_observability_metrics(self, card: Card, s: RuntimeSnapshot, stats: Dict[str, Any]) -> None:
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        for col in range(6):
            body.grid_columnconfigure(col, weight=1)
        items = [
            ("总事件", stats.get("total_events", len(getattr(s, "trace_records", []) or [])), COLORS["accent"]),
            ("工具", stats.get("tool_events", 0), COLORS["text_main"]),
            ("质量门", stats.get("quality_gate_events", 0), COLORS["warning"]),
            ("审计", stats.get("audit_events", 0), COLORS["text_main"]),
            ("错误", stats.get("error_events", 0), COLORS["danger"] if int(stats.get("error_events", 0) or 0) else COLORS["success"]),
            ("待确认", stats.get("pending_confirmations", s.pending_confirmation_count), COLORS["warning"]),
        ]
        for idx, (label, value, color) in enumerate(items):
            box = tk.Frame(body, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            box.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 8, 0))
            tk.Label(box, text=str(value), bg=COLORS["bg_card_2"], fg=color, font=FONTS["number"]).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(box, text=label, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(anchor="w", padx=10, pady=(0, 8))
        make_hint(body, f"contract={safe_text(getattr(s, 'observability_contract', ''), 90)} · export_digest={safe_text(getattr(s, 'trace_export_digest', ''), 32) or 'pending'}", bg=COLORS["bg_card"], wraplength=980).grid(row=1, column=0, columnspan=6, sticky="ew", pady=(10, 0))

    def _populate_trace_table(self, card: Card, records: List[Any]) -> None:
        table = tk.Frame(card, bg=COLORS["bg_card"])
        table.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 14))
        headers = ["seq", "category", "event", "phase/status", "ref", "message"]
        widths = [6, 12, 18, 22, 22, 44]
        for col, (header, width) in enumerate(zip(headers, widths)):
            table.grid_columnconfigure(col, weight=1 if col in (3, 5) else 0)
            tk.Label(table, text=header, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], width=width, anchor="w", padx=6, pady=6).grid(row=0, column=col, sticky="ew", padx=(0, 1), pady=(0, 1))
        if not records:
            make_hint(table, "暂无 Trace 记录。真实 Runtime SSE 或 Mock 投影到达后显示。", bg=COLORS["bg_card"]).grid(row=1, column=0, columnspan=len(headers), sticky="w", pady=12)
            return
        for r, rec in enumerate(records[-80:], start=1):
            seq = getattr(rec, "seq", "")
            category = safe_text(getattr(rec, "category", "runtime"), 40)
            event = safe_text(getattr(rec, "source_event", getattr(rec, "event_type", "runtime_state")), 80)
            phase = safe_text(getattr(rec, "phase", "") or getattr(rec, "status", ""), 120)
            ref = safe_text(getattr(rec, "audit_ref", "") or getattr(rec, "gate_ref", "") or getattr(rec, "rollback_ref", "") or getattr(rec, "run_id_digest", ""), 80)
            message = safe_text(getattr(rec, "message", "") or getattr(rec, "decision", ""), 160)
            color = COLORS["danger"] if category == "error" else COLORS["warning"] if category == "quality_gate" else COLORS["text_main"]
            for c, value in enumerate([seq, category, event, phase, ref, message]):
                tk.Label(table, text=safe_text(value, 160), bg=COLORS["bg_card"], fg=color if c in (1, 5) else COLORS["text_main"], font=FONTS["small"], anchor="w", padx=6, pady=6, wraplength=280 if c == 5 else 160).grid(row=r, column=c, sticky="ew", padx=(0, 1), pady=(0, 1))

    # ------------------------------------------------------------------- hooks
    def _build_hooks_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(
            root,
            "HookBus 确定性规则层",
            "L6.63：只读展示请求守卫、事件守卫、A5 阻断、SSE 收口检查与 Hook 记录；不产生前端执行权限。",
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(1, weight=1)

        stats = dict(getattr(s, "hook_stats", {}) or {})
        metrics = Card(body, "Hook 指标")
        metrics.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        self._populate_hook_metrics(metrics, s, stats)

        table = Card(body, "Hook 决策记录")
        table.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        self._populate_hook_table(table, list(getattr(s, "hook_records", []) or []))

        side = tk.Frame(body, bg=COLORS["bg_root"], width=380)
        side.grid(row=1, column=1, sticky="nsew")
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)

        boundary = Card(side, "确定性边界")
        boundary.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        rules = [
            "HookBus 仅校验请求/事件，不执行命令",
            "前端不可调用 Provider SDK 或工具",
            "前端不可写长期记忆、审计、回滚",
            "A5 必须 blocked 或 requires_confirmation",
            "run_terminal 必须在 assistant_final 之后",
            "HookRecord 只保留 digest / configured / 摘要",
        ]
        for idx, rule in enumerate(rules, start=1):
            tk.Label(boundary, text=f"✓ {rule}", bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["small"]).grid(row=idx, column=0, sticky="w", padx=14, pady=(8 if idx == 1 else 4, 0))
        tk.Button(boundary, text="查看 Hook 详情", command=self._show_hook_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=len(rules) + 1, column=0, sticky="w", padx=14, pady=(12, 14))

        blocker = Card(side, "最近阻断")
        blocker.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        last_blocker = safe_text(getattr(s, "hook_last_blocker", "") or stats.get("last_blocker", ""), 220)
        LabeledValue(blocker, "状态", "有阻断" if last_blocker else "无阻断", COLORS["danger"] if last_blocker else COLORS["success"]).grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 4))
        make_hint(blocker, last_blocker or "暂无 HookBus 阻断；如果真实 Runtime 返回 A5 allowed 或 run_terminal 顺序错误，会在这里显示。", bg=COLORS["bg_card"], wraplength=330).grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 14))

        policy = Card(side, "规则覆盖")
        policy.grid(row=2, column=0, sticky="ew")
        stages = ["pre_chat_submit", "pre_provider_settings_submit", "pre_confirmation_submit", "pre_control_request", "pre_event_apply", "post_event_apply", "pre_finalize", "on_error"]
        for idx, stage in enumerate(stages, start=1):
            tk.Label(policy, text=f"• {stage}", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=idx, column=0, sticky="w", padx=14, pady=(6 if idx == 1 else 3, 0))

    def _populate_hook_metrics(self, card: Card, s: RuntimeSnapshot, stats: Dict[str, Any]) -> None:
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        for col in range(5):
            body.grid_columnconfigure(col, weight=1)
        items = [
            ("总 Hook", stats.get("total_hooks", len(getattr(s, "hook_records", []) or [])), COLORS["accent"]),
            ("允许", stats.get("allow_count", 0), COLORS["success"]),
            ("警告", stats.get("warn_count", 0), COLORS["warning"]),
            ("阻断", stats.get("block_count", 0), COLORS["danger"] if int(stats.get("block_count", 0) or 0) else COLORS["success"]),
            ("最后", safe_text(stats.get("last_verdict", "none"), 16), COLORS["text_main"]),
        ]
        for idx, (label, value, color) in enumerate(items):
            box = tk.Frame(body, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            box.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 8, 0))
            tk.Label(box, text=str(value), bg=COLORS["bg_card_2"], fg=color, font=FONTS["number"]).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(box, text=label, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(anchor="w", padx=10, pady=(0, 8))
        make_hint(body, f"contract={safe_text(getattr(s, 'hook_bus_contract', ''), 90)} · digest={safe_text(getattr(s, 'hook_export_digest', ''), 32) or 'pending'}", bg=COLORS["bg_card"], wraplength=980).grid(row=1, column=0, columnspan=5, sticky="ew", pady=(10, 0))

    def _populate_hook_table(self, card: Card, records: List[Any]) -> None:
        table = tk.Frame(card, bg=COLORS["bg_card"])
        table.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 14))
        headers = ["seq", "stage", "rule", "verdict", "event", "reason"]
        widths = [6, 22, 24, 10, 18, 48]
        for col, (header, width) in enumerate(zip(headers, widths)):
            table.grid_columnconfigure(col, weight=1 if col in (1, 2, 5) else 0)
            tk.Label(table, text=header, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], width=width, anchor="w", padx=6, pady=6).grid(row=0, column=col, sticky="ew", padx=(0, 1), pady=(0, 1))
        if not records:
            make_hint(table, "暂无 Hook 记录。SSE / 设置 / 确认 / 控制请求进入后显示。", bg=COLORS["bg_card"]).grid(row=1, column=0, columnspan=len(headers), sticky="w", pady=12)
            return
        for r, rec in enumerate(records[-80:], start=1):
            seq = getattr(rec, "seq", "")
            stage = safe_text(getattr(rec, "stage", ""), 80)
            rule = safe_text(getattr(rec, "rule_id", ""), 100)
            verdict = safe_text(getattr(rec, "verdict", ""), 40)
            event = safe_text(getattr(rec, "source_event", ""), 80)
            reason = safe_text(getattr(rec, "reason", ""), 180)
            color = COLORS["danger"] if verdict == "block" else COLORS["warning"] if verdict == "warn" else COLORS["text_main"]
            for c, value in enumerate([seq, stage, rule, verdict, event, reason]):
                tk.Label(table, text=safe_text(value, 180), bg=COLORS["bg_card"], fg=color if c in (3, 5) else COLORS["text_main"], font=FONTS["small"], anchor="w", padx=6, pady=6, wraplength=300 if c == 5 else 170).grid(row=r, column=c, sticky="ew", padx=(0, 1), pady=(0, 1))

    def _build_memory_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        self._page_header(root, "记忆", "只展示 sanitized_summary、digest、evidence_ref，不展示原始记忆正文。").grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        summary = Card(body, "记忆摘要")
        summary.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        make_hint(summary, s.memory_sanitized_summary or "暂无记忆摘要。", bg=COLORS["bg_card"]).grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 12))
        LabeledValue(summary, "digest", s.memory_digest or "无").grid(row=2, column=0, sticky="ew", padx=14, pady=4)
        LabeledValue(summary, "evidence_ref", s.memory_evidence_ref or "无").grid(row=3, column=0, sticky="ew", padx=14, pady=(4, 14))

        boundary = Card(body, "显示边界")
        boundary.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        rules = ["不展示原始记忆正文", "不展示隐私原文", "不展示完整会话记录", "不展示未脱敏证据", "只消费 PublicProjection / 摘要级 ref"]
        for idx, rule in enumerate(rules, start=1):
            tk.Label(boundary, text=f"✓ {rule}", bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["body"]).grid(row=idx, column=0, sticky="w", padx=14, pady=(8 if idx == 1 else 4, 0))

    # ------------------------------------------------------------- iteration
    def _build_iteration_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(root, "自我迭代区", "展示由用户沟通、失败复盘、学习缺口生成的迭代候选；确认后仍走 Planner / ExecutionSpine / QualityGate。") .grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)

        candidates = Card(body, "迭代候选")
        candidates.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        candidates.grid_columnconfigure(0, weight=1)
        projection = s.self_iteration_projection
        if not projection.candidates:
            make_hint(candidates, "暂无自我迭代候选。", bg=COLORS["bg_card"]).grid(row=1, column=0, sticky="ew", padx=14, pady=14)
        for idx, item in enumerate(projection.candidates[:8], start=1):
            item_frame = tk.Frame(candidates, bg=COLORS["bg_card"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            item_frame.grid(row=idx, column=0, sticky="ew", padx=14, pady=(8 if idx == 1 else 6, 0))
            item_frame.grid_columnconfigure(0, weight=1)
            tk.Label(item_frame, text=f"{item.candidate_id} · {item.risk_level}", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 0))
            tk.Label(item_frame, text=item.title, bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["body_bold"], wraplength=560, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(3, 4))
            make_hint(item_frame, f"来源：{item.source}；预计改动：{item.expected_change}", bg=COLORS["bg_card"], wraplength=580).grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 4))
            LabeledValue(item_frame, "回滚", item.rollback_plan).grid(row=3, column=0, sticky="ew", padx=10, pady=2)
            LabeledValue(item_frame, "测试", item.test_requirement).grid(row=4, column=0, sticky="ew", padx=10, pady=2)
            btns = tk.Frame(item_frame, bg=COLORS["bg_card"])
            btns.grid(row=5, column=0, sticky="w", padx=10, pady=(8, 10))
            if item.status == "pending_user_confirmation":
                tk.Button(btns, text="确认进入迭代", command=lambda cid=item.candidate_id: self._submit_iteration_confirmation(cid, "confirmed"), bg=COLORS["success"], fg="#FFFFFF", relief="flat", padx=12, pady=5).pack(side="left", padx=(0, 8))
                tk.Button(btns, text="暂不处理", command=lambda cid=item.candidate_id: self._submit_iteration_confirmation(cid, "rejected"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=12, pady=5).pack(side="left")
            else:
                tk.Label(btns, text=f"前端状态：{item.status}", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(side="left")

        side = tk.Frame(body, bg=COLORS["bg_root"], width=340)
        side.grid(row=0, column=1, sticky="nsew")
        side.grid_propagate(False)
        status = Card(side, "迭代边界")
        status.grid(row=0, column=0, sticky="ew")
        rules = [
            f"面板状态：{projection.panel_status}",
            f"待确认：{projection.pending_count}",
            f"更新时间：{projection.last_updated}",
            "用户确认后只生成票据",
            "真实更新仍走质量门",
            "必须有回滚点",
        ]
        for idx, rule in enumerate(rules, start=1):
            tk.Label(status, text=f"✓ {rule}", bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["body"]).grid(row=idx, column=0, sticky="w", padx=14, pady=(8 if idx == 1 else 4, 0))

    # ------------------------------------------------------------- four paths
    def _build_four_paths_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        self._page_header(root, "四主路径状态", "执行、记忆、情志、生命周期统一投影；只展示摘要和 digest，不展示散对象。") .grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        for col in range(2):
            body.grid_columnconfigure(col, weight=1)
        status = s.four_path_status
        cards = [
            ("执行路径", status.execution_status),
            ("记忆路径", status.memory_status),
            ("情志路径", status.affective_status),
            ("生命周期路径", status.lifecycle_status),
        ]
        for idx, (title, content) in enumerate(cards):
            card = Card(body, title)
            card.grid(row=idx // 2, column=idx % 2, sticky="nsew", padx=(0 if idx % 2 == 0 else 8, 8 if idx % 2 == 0 else 0), pady=(0, 16))
            make_hint(card, content, bg=COLORS["bg_card"], wraplength=440).grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14))
        digest = Card(body, "统一 PlannerContext")
        digest.grid(row=2, column=0, columnspan=2, sticky="ew")
        LabeledValue(digest, "context_digest", status.planner_context_digest).grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 4))
        make_hint(digest, status.hard_boundary_summary, bg=COLORS["bg_card"]).grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 14))

    # ------------------------------------------------------------- installer
    def _build_installer_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(root, "安装器 / 打包器 RC 前置结构", "L6.69：安装 manifest、版本槽、启动自检、打包 dry-run、发布 manifest 与签名策略占位；不是最终 exe/msi 安装包。").grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(1, weight=1)

        manifest = getattr(s, "installer_manifest", None)
        checks = list(getattr(s, "startup_self_checks", []) or [])
        slots = list(getattr(s, "version_slots", []) or [])
        crashes = list(getattr(s, "crash_report_records", []) or [])
        repairs = list(getattr(s, "repair_action_records", []) or [])

        metrics = Card(body, "安装器指标")
        metrics.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        mbody = tk.Frame(metrics, bg=COLORS["bg_card"])
        mbody.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        items = [
            ("阶段", safe_text(getattr(s, "installer_stage", "rc_preinstall"), 18), COLORS["accent"]),
            ("版本槽", len(slots), COLORS["text_main"]),
            ("自检项", len(checks), COLORS["text_main"]),
            ("回滚", "ready" if getattr(manifest, "rollback_ready", True) else "blocked", COLORS["success"] if getattr(manifest, "rollback_ready", True) else COLORS["danger"]),
            ("修复", "available" if getattr(manifest, "offline_repair_available", True) else "none", COLORS["warning"]),
            ("打包器", "dry-run", COLORS["warning"]),
        ]
        for col in range(len(items)):
            mbody.grid_columnconfigure(col, weight=1)
        for idx, (label, value, color) in enumerate(items):
            box = tk.Frame(mbody, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            box.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 8, 0))
            tk.Label(box, text=str(value), bg=COLORS["bg_card_2"], fg=color, font=FONTS["number"]).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(box, text=label, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(anchor="w", padx=10, pady=(0, 8))
        make_hint(mbody, f"contract={safe_text(getattr(s, 'installer_rc_contract', ''), 100)} · channel={safe_text(getattr(s, 'update_channel', ''), 40)} · {safe_text(getattr(s, 'installer_last_message', ''), 180)}", bg=COLORS["bg_card"], wraplength=980).grid(row=1, column=0, columnspan=len(items), sticky="ew", pady=(10, 0))

        slots_card = Card(body, "版本槽 / 回滚槽")
        slots_card.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        slot_body = tk.Frame(slots_card, bg=COLORS["bg_card"])
        slot_body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 14)); slot_body.grid_columnconfigure(0, weight=1)
        if not slots:
            make_hint(slot_body, "暂无版本槽投影。", bg=COLORS["bg_card"]).grid(row=0, column=0, sticky="ew")
        for idx, slot in enumerate(slots[:12], start=1):
            row = tk.Frame(slot_body, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            row.grid(row=idx, column=0, sticky="ew", pady=(0, 8)); row.grid_columnconfigure(0, weight=1)
            title = f"{safe_text(getattr(slot, 'slot_name', ''), 60)} · {safe_text(getattr(slot, 'state', ''), 30)} · {safe_text(getattr(slot, 'version_label', ''), 80)}"
            tk.Label(row, text=title, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
            msg = f"path_digest={safe_text(getattr(slot, 'path_digest', ''), 40)} · rollback={getattr(slot, 'rollback_capable', False)} · verified={safe_text(getattr(slot, 'last_verified', ''), 60)} · {safe_text(getattr(slot, 'message', ''), 140)}"
            tk.Label(row, text=msg, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=760, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))

        side = tk.Frame(body, bg=COLORS["bg_root"], width=380)
        side.grid(row=1, column=1, sticky="nsew")
        side.grid_propagate(False)
        checks_card = Card(side, "启动自检")
        checks_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        if not checks:
            make_hint(checks_card, "暂无启动自检记录。", bg=COLORS["bg_card"]).grid(row=1, column=0, sticky="ew", padx=14, pady=12)
        for idx, check in enumerate(checks[:8], start=1):
            status = safe_text(getattr(check, "status", "pending"), 40)
            color = COLORS["success"] if status == "pass" else COLORS["danger"] if status in {"fail", "blocked"} else COLORS["warning"] if status == "warn" else COLORS["text_sub"]
            LabeledValue(checks_card, safe_text(getattr(check, "name", "check"), 40), f"{status} · {safe_text(getattr(check, 'message', ''), 70)}", color).grid(row=idx, column=0, sticky="ew", padx=14, pady=(8 if idx == 1 else 4, 0))
        btn_row = tk.Frame(checks_card, bg=COLORS["bg_card"])
        btn_row.grid(row=min(len(checks), 8) + 1, column=0, sticky="w", padx=14, pady=(12, 14))
        tk.Button(btn_row, text="自检详情", command=self._show_installer_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="刷新", command=lambda: self.show_page("installer"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).pack(side="left")

        repair_card = Card(side, "崩溃 / 离线修复")
        repair_card.grid(row=1, column=0, sticky="ew")
        for idx, crash in enumerate(crashes[:2], start=1):
            LabeledValue(repair_card, "崩溃报告", f"{safe_text(getattr(crash, 'status', ''), 40)} · count={getattr(crash, 'crash_count', 0)} · local_only={getattr(crash, 'local_only', True)}").grid(row=idx, column=0, sticky="ew", padx=14, pady=(8 if idx == 1 else 4, 0))
        base = max(1, len(crashes[:2])) + 1
        for j, action in enumerate(repairs[:4], start=base):
            LabeledValue(repair_card, safe_text(getattr(action, "title", "repair"), 40), f"{safe_text(getattr(action, 'status', ''), 40)} · no_frontend_apply={getattr(action, 'no_frontend_apply', True)}").grid(row=j, column=0, sticky="ew", padx=14, pady=(8 if j == base else 4, 0))
        tk.Button(repair_card, text="安装器边界", command=self._show_installer_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=base + len(repairs[:4]), column=0, sticky="w", padx=14, pady=(12, 14))

    # ---------------------------------------------------------------- settings
    def _build_settings_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(root, "设置", "API 输入口、主模型选择、模型搜索均集中在设置页；Runtime 只通过 L6.57 后端契约端点接线。") .grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        model_card = Card(body, "API 与主模型")
        model_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._populate_api_model_settings(model_card)

        status = Card(body, "RuntimeClient 状态")
        status.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        identity = self._get_product_identity_public()
        provider_settings = self._get_provider_settings_public()
        status_items = [
            ("source_kind", s.source_kind),
            ("runtime_status", s.runtime_status),
            ("model_provider", s.model_provider),
            ("planner_mode", s.planner_mode),
            ("tool_execution_mode", s.tool_execution_mode),
            ("connection_status", s.connection_status),
            ("metadata_endpoint", identity.get("endpoint") or identity.get("metadata_endpoint") or PRODUCT_IDENTITY.metadata_endpoint),
            ("unique_developer", identity.get("unique_developer") or PRODUCT_IDENTITY.unique_developer),
            ("angel_investor", identity.get("angel_investor") or PRODUCT_IDENTITY.angel_investor),
            ("provider_public", provider_settings.get("provider", "未读取")),
            ("model_public", provider_settings.get("model", "未读取")),
            ("provider_config_state", provider_settings.get("status") or provider_settings.get("provider_config_state") or getattr(s, "provider_config_state", "未提交")),
            ("config_error_code", provider_settings.get("config_error_code") or getattr(s, "provider_config_error_code", "无") or "无"),
            ("config_audit_id", provider_settings.get("audit_id") or getattr(s, "provider_config_audit_id", "无") or "无"),
            ("api_key_configured", str(provider_settings.get("api_key_configured", getattr(s, "provider_api_key_configured", "未读取")))),
            ("api_key_digest", provider_settings.get("api_key_digest") or getattr(s, "provider_api_key_digest", "未读取") or "未配置"),
            ("base_url_configured", str(provider_settings.get("base_url_configured", getattr(s, "provider_base_url_configured", "未读取")))),
            ("base_url_digest", provider_settings.get("base_url_digest") or getattr(s, "provider_base_url_digest", "未读取") or "未配置"),
            ("config_message", provider_settings.get("message") or getattr(s, "provider_config_message", "未读取")),
        ]
        for idx, (label, value) in enumerate(status_items, start=1):
            LabeledValue(status, label, value).grid(row=idx, column=0, sticky="ew", padx=14, pady=(8 if idx == 1 else 4, 0))

        policy = Card(body, "安全边界")
        policy.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(16, 0))
        policy_items = [
            "API Key/Base URL 输入只在设置页", "Key/Base URL 写入 Runtime 后只显示 configured/digest", "不在首页/任务栏显示 API 明文", "不裸调模型/Provider SDK", "不调用 Adapter", "不直接执行工具", "不写 tiangong_kernel", "Provider 设置只向 /settings/provider 提交写入请求", "Runtime 对话只走 /chat/stream-events",
        ]
        for idx, item in enumerate(policy_items, start=1):
            tk.Label(policy, text=f"✓ {item}", bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["body"]).grid(row=idx, column=0, sticky="w", padx=14, pady=(8 if idx == 1 else 4, 0))

        operations = Card(body, "前端操作占位")
        operations.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(16, 0))
        make_hint(operations, "Mock/JSON 模式只刷新本地快照；SSE 模式只连接 L6.57 后端契约端点，不裸调 Provider/工具/记忆/审计。", bg=COLORS["bg_card"]).grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 10))
        btns = tk.Frame(operations, bg=COLORS["bg_card"])
        btns.grid(row=2, column=0, sticky="w", padx=14, pady=(0, 14))
        tk.Button(btns, text="刷新快照 F5", command=self._refresh_snapshot_frontend_only, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=14, pady=6).pack(side="left", padx=(0, 10))
        tk.Button(btns, text="导出前端快照", command=self._export_snapshot_frontend_only, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=14, pady=6).pack(side="left", padx=(0, 10))
        tk.Button(btns, text="查看安全边界", command=self._show_boundary_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=14, pady=6).pack(side="left")

    def _populate_api_model_settings(self, card: Card) -> None:
        form = tk.Frame(card, bg=COLORS["bg_card"])
        form.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14))
        form.grid_columnconfigure(1, weight=1)

        labels = [
            ("Provider", self.api_provider_var),
            ("API Base URL", self.api_base_url_var),
            ("API Key", self.api_key_var),
            ("主模型", self.main_model_var),
            ("模型搜索", self.model_search_var),
        ]
        for idx, (label, var) in enumerate(labels):
            tk.Label(form, text=label, bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=idx, column=0, sticky="w", pady=5)
            if label == "Provider":
                widget = ttk.Combobox(form, textvariable=var, values=["deepseek", "qwen", "zhipu", "openai", "custom"], state="readonly")
            elif label == "API Key":
                widget = tk.Entry(form, textvariable=var, show="•", bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat")
            else:
                widget = tk.Entry(form, textvariable=var, bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat")
            widget.grid(row=idx, column=1, sticky="ew", padx=(10, 0), pady=5, ipady=5)

        model_box = tk.Listbox(form, height=5, bg=COLORS["bg_input"], fg=COLORS["text_main"], highlightbackground=COLORS["border_soft"], selectbackground=COLORS["accent"], relief="flat")
        model_box.grid(row=len(labels), column=0, columnspan=2, sticky="ew", pady=(8, 6))
        for item in filter_model_catalog(self.model_search_var.get()):
            model_box.insert("end", f"{item.provider} · {item.model_id} · {item.display_name}")
        model_box.bind("<<ListboxSelect>>", lambda event, box=model_box: self._select_model_from_listbox(box))

        btns = tk.Frame(form, bg=COLORS["bg_card"])
        btns.grid(row=len(labels) + 1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        tk.Button(btns, text="搜索/刷新列表", command=lambda: self.show_page("settings"), bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=12, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="保存设置", command=self._save_runtime_settings_frontend_only, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=12, pady=5).pack(side="left")
        tk.Label(form, textvariable=self.settings_status_var, bg=COLORS["bg_card"], fg=COLORS["text_weak"], font=FONTS["small"], wraplength=430, justify="left").grid(row=len(labels) + 2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    def _get_product_identity_public(self) -> Dict[str, Any]:
        getter = getattr(self.client, "get_product_identity", None)
        if callable(getter):
            try:
                data = getter() or {}
                if isinstance(data, dict):
                    return {safe_text(k, 80): safe_text(v, 160) for k, v in data.items()}
            except Exception as exc:
                return {**PRODUCT_IDENTITY.to_dict(), "read_error": safe_text(exc, 160)}
        return PRODUCT_IDENTITY.to_dict()

    def _get_provider_settings_public(self) -> Dict[str, Any]:
        getter = getattr(self.client, "get_provider_settings", None)
        if callable(getter):
            try:
                data = getter() or {}
                if isinstance(data, dict):
                    allowed = {"provider", "model", "base_url_digest", "base_url_configured", "api_key_digest", "api_key_configured", "timeout", "stream", "planner_mode", "tool_execution_mode", "status", "provider_config_state", "config_error_code", "message", "audit_id", "requires_restart", "frontend_contract"}
                    return {safe_text(k, 80): safe_text(v, 160) for k, v in data.items() if k in allowed}
            except Exception as exc:
                return {"read_error": safe_text(exc, 160)}
        return {}

    # ---------------------------------------------------------- shared cards
    def _page_header(self, root: tk.Misc, title: str, subtitle: str) -> tk.Frame:
        frame = tk.Frame(root, bg=COLORS["bg_root"])
        frame.grid_columnconfigure(0, weight=1)
        make_section_title(frame, title).grid(row=0, column=0, sticky="w")
        tk.Label(frame, text=subtitle, bg=COLORS["bg_root"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=1, column=0, sticky="w", pady=(4, 0))
        return frame

    def _build_files_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        wrap = tk.Frame(root, bg=COLORS["bg_root"])
        wrap.grid(row=0, column=0, sticky="nsew", padx=DIMENS["page_pad"], pady=DIMENS["page_pad"])
        wrap.grid_columnconfigure(0, weight=1)
        header = self._page_header(wrap, "文件传输", "上传/下载都必须走 Runtime / TiangongWangguan 授权链路；前端只提交脱敏请求与展示回执。")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        action_card = Card(wrap, "文件入口")
        action_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        body = tk.Frame(action_card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        make_hint(
            body,
            "选择本地文件后，前端只计算文件名、大小、摘要和用途，向 Runtime 提交 transfer request；不把原始路径、文件正文、密钥或端点写入报告。",
            bg=COLORS["bg_card"],
            wraplength=760,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        btn_row = tk.Frame(body, bg=COLORS["bg_card"])
        btn_row.grid(row=1, column=0, sticky="w")
        tk.Button(btn_row, text="选择文件并提交", command=self._request_file_transfer_from_dialog, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=16, pady=7).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="先申请工作区授权", command=lambda: self.show_page("workspace"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=14, pady=7).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="刷新回执", command=lambda: self.show_page("files"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=14, pady=7).pack(side="left")

        records_card = Card(wrap, "最近文件传输回执")
        records_card.grid(row=2, column=0, sticky="ew")
        records = list(getattr(s, "file_transfer_records", []) or [])[-8:]
        inner = tk.Frame(records_card, bg=COLORS["bg_card"])
        inner.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        inner.grid_columnconfigure(0, weight=1)
        if not records:
            make_hint(inner, "暂无文件传输记录。", bg=COLORS["bg_card"]).grid(row=0, column=0, sticky="ew")
        for idx, rec in enumerate(records):
            row = tk.Frame(inner, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            row.grid(row=idx, column=0, sticky="ew", pady=(0, 8))
            row.grid_columnconfigure(0, weight=1)
            title = f"{safe_text(getattr(rec, 'file_name', 'attachment'), 80)} · {getattr(rec, 'size_bytes', 0)} bytes · {safe_text(getattr(rec, 'status', ''), 40)}"
            tk.Label(row, text=title, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
            msg = f"digest={safe_text(getattr(rec, 'sha256_digest', ''), 24) or '无'} · audit={safe_text(getattr(rec, 'audit_id', ''), 32) or '无'} · {safe_text(getattr(rec, 'message', ''), 160)}"
            tk.Label(row, text=msg, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=760, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
        tk.Button(records_card, text="文件传输边界详情", command=self._show_file_transfer_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 14))



    def _build_connectors_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        wrap = tk.Frame(root, bg=COLORS["bg_root"])
        wrap.grid(row=0, column=0, sticky="nsew", padx=DIMENS["page_pad"], pady=DIMENS["page_pad"])
        wrap.grid_columnconfigure(0, weight=1)
        header = self._page_header(wrap, "MCP / 连接器注册表", "白名单、签名摘要、隔离状态和注册请求只读展示；前端不安装、不执行、不存密钥、不直连 MCP 市场。")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        policy_card = Card(wrap, "注册表策略")
        policy_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        projection = getattr(s, "connector_registry_projection", None)
        body = tk.Frame(policy_card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        values = [
            ("状态", safe_text(getattr(s, "connector_registry_state", "ready"), 80)),
            ("默认模式", safe_text(getattr(projection, "default_mode", "disabled"), 40)),
            ("连接器数量", str(getattr(projection, "connector_count", 0))),
            ("只读默认", str(getattr(projection, "read_only_count", 0))),
            ("隔离数量", str(getattr(projection, "quarantined_count", 0))),
            ("开放市场安装", "禁止"),
            ("前端安装/执行", "禁止"),
            ("前端密钥存储", "禁止"),
        ]
        for idx, (name, value) in enumerate(values):
            LabeledValue(body, name, value, COLORS["text_main"]).grid(row=idx, column=0, sticky="ew", pady=3)

        register_card = Card(wrap, "注册请求")
        register_card.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        req_body = tk.Frame(register_card, bg=COLORS["bg_card"])
        req_body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        req_body.grid_columnconfigure(1, weight=1)
        make_hint(req_body, "提交时只生成 connector registration envelope：display_name、kind、manifest_digest、source_digest、scopes。不会保存原始 endpoint、密钥、manifest 正文，也不会安装 MCP server。", bg=COLORS["bg_card"], wraplength=760).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        tk.Label(req_body, text="名称", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=1, column=0, sticky="w", pady=4)
        self.connector_name_var = tk.StringVar(value="本地 MCP 候选连接器")
        tk.Entry(req_body, textvariable=self.connector_name_var, bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat").grid(row=1, column=1, sticky="ew", pady=4)
        tk.Label(req_body, text="类型", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=2, column=0, sticky="w", pady=4)
        self.connector_kind_var = tk.StringVar(value="mcp_server")
        ttk.Combobox(req_body, textvariable=self.connector_kind_var, values=("mcp_server", "local_connector", "remote_connector", "document_connector", "browser_connector", "workflow_connector"), state="readonly").grid(row=2, column=1, sticky="ew", pady=4)
        btn_row = tk.Frame(req_body, bg=COLORS["bg_card"])
        btn_row.grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))
        tk.Button(btn_row, text="提交注册请求", command=self._request_connector_registration, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=16, pady=7).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="刷新", command=lambda: self.show_page("connectors"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=14, pady=7).pack(side="left")

        records_card = Card(wrap, "注册 / 隔离回执")
        records_card.grid(row=3, column=0, sticky="ew")
        inner = tk.Frame(records_card, bg=COLORS["bg_card"])
        inner.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        inner.grid_columnconfigure(0, weight=1)
        records = list(getattr(s, "connector_registration_records", []) or [])[-8:]
        manifests = list(getattr(s, "connector_manifests", []) or [])[-8:]
        row_idx = 0
        if not records and not manifests:
            make_hint(inner, "暂无连接器注册或隔离记录。", bg=COLORS["bg_card"]).grid(row=0, column=0, sticky="ew")
        for rec in records:
            row = tk.Frame(inner, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            row.grid(row=row_idx, column=0, sticky="ew", pady=(0, 8)); row.grid_columnconfigure(0, weight=1); row_idx += 1
            title = f"注册 · {safe_text(getattr(rec, 'display_name', ''), 80)} · {safe_text(getattr(rec, 'kind', ''), 40)} · {safe_text(getattr(rec, 'status', ''), 40)}"
            tk.Label(row, text=title, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
            msg = f"manifest_digest={safe_text(getattr(rec, 'manifest_digest', ''), 24) or '无'} · trust={safe_text(getattr(rec, 'trust_level', ''), 40)} · audit={safe_text(getattr(rec, 'audit_id', ''), 32) or '无'} · {safe_text(getattr(rec, 'message', ''), 160)}"
            tk.Label(row, text=msg, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=760, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
        for item in manifests:
            row = tk.Frame(inner, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            row.grid(row=row_idx, column=0, sticky="ew", pady=(0, 8)); row.grid_columnconfigure(0, weight=1); row_idx += 1
            title = f"Manifest · {safe_text(getattr(item, 'display_name', ''), 80)} · {safe_text(getattr(item, 'default_mode', ''), 40)} · quarantine={getattr(item, 'quarantined', False)}"
            tk.Label(row, text=title, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
            msg = f"kind={safe_text(getattr(item, 'kind', ''), 40)} · digest={safe_text(getattr(item, 'manifest_digest', ''), 24)} · scopes={safe_text(','.join(getattr(item, 'requested_scopes', []) or []), 120)}"
            tk.Label(row, text=msg, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=760, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
        tk.Button(records_card, text="连接器边界详情", command=self._show_connector_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 14))

    def _build_workspace_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        wrap = tk.Frame(root, bg=COLORS["bg_root"])
        wrap.grid(row=0, column=0, sticky="nsew", padx=DIMENS["page_pad"], pady=DIMENS["page_pad"])
        wrap.grid_columnconfigure(0, weight=1)
        header = self._page_header(wrap, "Agent Workspace / 沙箱边界", "工作区、目录白名单、文件授权和下载中转只读展示；前端只提交授权请求，不创建工作区、不改 ACL、不复制文件。")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        policy_card = Card(wrap, "工作区策略")
        policy_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        policy = getattr(s, "workspace_policy", None)
        body = tk.Frame(policy_card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        values = [
            ("状态", safe_text(getattr(s, "workspace_state", "ready"), 80)),
            ("Root digest", safe_text(getattr(policy, "root_digest", "") or "未公开", 32)),
            ("默认模式", safe_text(getattr(policy, "default_mode", "read"), 32)),
            ("写入需确认", "是" if getattr(policy, "allow_write_requires_confirmation", True) else "否"),
            ("前端创建工作区", "禁止"),
            ("前端改 ACL", "禁止"),
            ("前端复制文件字节", "禁止"),
        ]
        for idx, (name, value) in enumerate(values):
            LabeledValue(body, name, value, COLORS["text_main"]).grid(row=idx, column=0, sticky="ew", pady=3)

        auth_card = Card(wrap, "文件授权请求")
        auth_card.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        auth_body = tk.Frame(auth_card, bg=COLORS["bg_card"])
        auth_body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        auth_body.grid_columnconfigure(0, weight=1)
        make_hint(auth_body, "选择文件后只生成授权 envelope：file_name、mode、scope、path_digest。不会把原始路径、文件正文或下载 token 写进前端报告。", bg=COLORS["bg_card"], wraplength=760).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        btn_row = tk.Frame(auth_body, bg=COLORS["bg_card"])
        btn_row.grid(row=1, column=0, sticky="w")
        tk.Button(btn_row, text="申请只读授权", command=lambda: self._request_file_authorization_from_dialog("read"), bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=16, pady=7).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="申请写入授权", command=lambda: self._request_file_authorization_from_dialog("write"), bg=COLORS["warning"], fg="#FFFFFF", relief="flat", padx=16, pady=7).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="刷新", command=lambda: self.show_page("workspace"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=14, pady=7).pack(side="left")

        records_card = Card(wrap, "最近授权 / 下载中转回执")
        records_card.grid(row=3, column=0, sticky="ew")
        inner = tk.Frame(records_card, bg=COLORS["bg_card"])
        inner.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        inner.grid_columnconfigure(0, weight=1)
        auth_records = list(getattr(s, "file_authorization_records", []) or [])[-6:]
        dl_records = list(getattr(s, "download_handoff_records", []) or [])[-4:]
        row_idx = 0
        if not auth_records and not dl_records:
            make_hint(inner, "暂无工作区授权或下载中转记录。", bg=COLORS["bg_card"]).grid(row=0, column=0, sticky="ew")
        for rec in auth_records:
            row = tk.Frame(inner, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            row.grid(row=row_idx, column=0, sticky="ew", pady=(0, 8)); row.grid_columnconfigure(0, weight=1); row_idx += 1
            title = f"授权 · {safe_text(getattr(rec, 'file_name', ''), 80)} · {safe_text(getattr(rec, 'mode', ''), 32)} · {safe_text(getattr(rec, 'status', ''), 40)}"
            tk.Label(row, text=title, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
            msg = f"scope={safe_text(getattr(rec, 'scope', ''), 60)} · path_digest={safe_text(getattr(rec, 'path_digest', ''), 24) or '无'} · audit={safe_text(getattr(rec, 'audit_id', ''), 32) or '无'} · {safe_text(getattr(rec, 'message', ''), 160)}"
            tk.Label(row, text=msg, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=760, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
        for rec in dl_records:
            row = tk.Frame(inner, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            row.grid(row=row_idx, column=0, sticky="ew", pady=(0, 8)); row.grid_columnconfigure(0, weight=1); row_idx += 1
            title = f"下载中转 · {safe_text(getattr(rec, 'file_name', ''), 80)} · {safe_text(getattr(rec, 'status', ''), 40)}"
            tk.Label(row, text=title, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
            msg = f"artifact_digest={safe_text(getattr(rec, 'artifact_id_digest', ''), 24)} · token_digest={safe_text(getattr(rec, 'download_token_digest', ''), 24)} · {safe_text(getattr(rec, 'message', ''), 160)}"
            tk.Label(row, text=msg, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=760, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
        tk.Button(records_card, text="工作区边界详情", command=self._show_workspace_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 14))

    def _populate_execution_status(self, card: Card, s: RuntimeSnapshot, compact: bool) -> None:
        tk.Label(card, text=s.execution_stage, bg=COLORS["bg_card"], fg=COLORS["accent"], font=FONTS["page_title"]).grid(row=1, column=0, sticky="w", padx=14, pady=(4, 10))
        for idx, step in enumerate(s.execution_steps[:3], start=2):
            StepItem(card, step.name, self._status_cn(step.status), step.status).grid(row=idx, column=0, sticky="ew", padx=14, pady=5)
        if compact:
            tk.Button(card, text="查看执行详情", command=lambda: self.show_page("execution"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=6, column=0, sticky="w", padx=14, pady=(10, 14))

    def _populate_quality(self, card: Card, s: RuntimeSnapshot, compact: bool) -> None:
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        LabeledValue(body, "决策", s.quality_decision, COLORS["success"] if s.quality_allow_continue else COLORS["danger"]).grid(row=0, column=0, sticky="ew", pady=4)
        LabeledValue(body, "允许继续", "是" if s.quality_allow_continue else "否", COLORS["success"] if s.quality_allow_continue else COLORS["danger"]).grid(row=1, column=0, sticky="ew", pady=4)
        if compact:
            tk.Button(
                body,
                text="查看质量门详情",
                command=self._show_quality_detail,
                bg=COLORS["bg_card_2"],
                fg=COLORS["text_sub"],
                relief="flat",
                padx=10,
                pady=5,
            ).grid(row=2, column=0, sticky="w", pady=(10, 0))
        else:
            LabeledValue(body, "允许打包", "是" if s.quality_allow_package else "否").grid(row=2, column=0, sticky="ew", pady=4)
            reasons = "；".join(s.blocking_reasons) if s.blocking_reasons else "无阻塞原因摘要"
            make_hint(body, safe_text(reasons, 220)).grid(row=3, column=0, sticky="ew", pady=(10, 0))

    def _populate_audit(self, card: Card, s: RuntimeSnapshot, compact: bool) -> None:
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        LabeledValue(body, "审计数量", str(s.audit_count)).grid(row=0, column=0, sticky="ew", pady=4)
        LabeledValue(body, "证据引用", s.evidence_ref).grid(row=1, column=0, sticky="ew", pady=4)
        if compact:
            tk.Button(body, text="审计详情", command=self._show_audit_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=2, column=0, sticky="w", pady=(10, 0))

    def _render_statusbar(self, s: RuntimeSnapshot) -> None:
        values = {
            "runtime_status": f"Runtime ● {s.runtime_status}",
            "provider_model": f"Provider {safe_text(getattr(s, 'provider_model', s.model_provider), 32)}",
            "budget_pool": f"Budget {safe_text(getattr(s, 'budget_pool', 'main_task'), 24)}",
            "budget_used_ratio": f"Used {safe_text(getattr(s, 'budget_used_ratio', '0%'), 12)}",
            "gate_status": f"Gate {safe_text(getattr(s, 'gate_status', s.quality_gate_status), 24)}",
            "audit_id": f"Audit {safe_text(getattr(s, 'audit_id', s.evidence_ref), 24)}",
            "memory_mode": f"Memory {safe_text(getattr(s, 'memory_mode', 'read_only'), 24)}",
            "tools_allowed": f"Tools {getattr(s, 'tools_allowed', 0)}",
            "latency_ms": f"Latency {getattr(s, 'latency_ms', 0)}ms",
        }
        for key, label in self.status_labels.items():
            label.configure(text=values.get(key, key))

    def _status_cn(self, status: str) -> str:
        return {
            "succeeded": "完成",
            "running": "进行中",
            "queued": "排队",
            "blocked": "阻塞",
            "failed": "失败",
            "confirmation_required": "待确认",
            "recovered": "已恢复",
            "timeout": "超时",
        }.get(status, status)


    # ---------------------------------------------------------- detail dialogs
    def _show_safe_detail(self, title: str, lines: Iterable[str]) -> None:
        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg=COLORS["bg_root"])
        win.geometry("640x420")
        win.minsize(520, 320)
        tk.Label(win, text=title, bg=COLORS["bg_root"], fg=COLORS["text_main"], font=FONTS["page_title"]).pack(anchor="w", padx=18, pady=(16, 8))
        text = tk.Text(win, bg=COLORS["bg_card"], fg=COLORS["text_main"], relief="flat", wrap="word", font=FONTS["body"], padx=12, pady=12)
        text.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        for line in lines:
            text.insert("end", safe_text(line, 420) + "\n")
        text.configure(state="disabled")
        tk.Button(win, text="关闭", command=win.destroy, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=18, pady=6).pack(anchor="e", padx=18, pady=(0, 16))

    def _show_frontend_notice(self, title: str, message: str) -> None:
        try:
            messagebox.showinfo(title, safe_text(message, 500), parent=self)
        except tk.TclError as exc:
            self._last_notice_error = safe_text(exc, 120)

    def _show_observability_detail(self) -> None:
        s = self.snapshot
        stats = dict(getattr(s, "trace_stats", {}) or {})
        lines = [
            f"contract：{safe_text(getattr(s, 'observability_contract', ''), 100)}",
            f"total_events：{stats.get('total_events', len(getattr(s, 'trace_records', []) or []))}",
            f"tool_events：{stats.get('tool_events', 0)}",
            f"quality_gate_events：{stats.get('quality_gate_events', 0)}",
            f"error_events：{stats.get('error_events', 0)}",
            f"terminal_order_valid：{getattr(s, 'trace_terminal_order_valid', True)}",
            f"export_digest：{safe_text(getattr(s, 'trace_export_digest', ''), 40) or 'pending'}",
            "",
            "最近 Trace：",
        ]
        for rec in list(getattr(s, "trace_records", []) or [])[-20:]:
            lines.append(f"- #{getattr(rec, 'seq', '')} {getattr(rec, 'category', '')}/{getattr(rec, 'source_event', '')} · {getattr(rec, 'phase', '')} · {getattr(rec, 'message', '')}")
        lines.append("")
        lines.append("边界：此详情只读展示脱敏 trace，不导出原始 prompt、密钥、端点、路径或工具参数。")
        self._show_safe_detail("运行观测详情", lines)

    def _show_quality_detail(self) -> None:
        s = self.snapshot
        reasons = s.blocking_reasons or ["无阻塞原因摘要。"]
        lines = [
            f"决策：{s.quality_decision}",
            f"允许继续：{'是' if s.quality_allow_continue else '否'}",
            f"允许打包：{'是' if s.quality_allow_package else '否'}",
            "",
            "阻塞摘要：",
            *[f"- {item}" for item in reasons],
            "",
            "边界：此处只展示质量门脱敏摘要。允许/拒绝/修改只会提交 Runtime 请求，前端不直接放行工具。",
        ]
        self._show_safe_detail("质量门详情（脱敏摘要）", lines)

    def _show_audit_detail(self) -> None:
        s = self.snapshot
        lines = [
            f"audit_count：{s.audit_count}",
            f"evidence_ref：{s.evidence_ref}",
            "",
            "边界：FE.01 只展示 evidence_ref 与审计数量，不展开完整审计链、prompt、密钥或真实路径；前端不写审计。",
        ]
        self._show_safe_detail("审计摘要（脱敏）", lines)

    def _show_recovery_detail(self) -> None:
        s = self.snapshot
        actions = s.recovery_next_actions or ["暂无下一步恢复动作。"]
        lines = [
            f"ticket_id：{s.recovery_ticket_id or '无'}",
            f"failure_count：{s.recovery_failure_count}",
            f"resume_plan_count：{s.recovery_resume_plan_count}",
            f"requires_human_confirmation：{'是' if s.recovery_requires_human_confirmation else '否'}",
            "",
            "next_actions：",
            *[f"- {item}" for item in actions],
            "",
            "边界：恢复续接按钮只展示摘要，不触发恢复执行。",
        ]
        self._show_safe_detail("恢复续接详情（占位）", lines)

    def _show_hook_detail(self) -> None:
        s = self.snapshot
        stats = dict(getattr(s, "hook_stats", {}) or {})
        lines = [
            "L6.63 HookBus 确定性规则层：",
            f"contract：{getattr(s, 'hook_bus_contract', '')}",
            f"hook_enabled：{getattr(s, 'hook_enabled', True)}",
            f"total_hooks：{stats.get('total_hooks', 0)}",
            f"allow/warn/block：{stats.get('allow_count', 0)} / {stats.get('warn_count', 0)} / {stats.get('block_count', 0)}",
            f"last_rule：{safe_text(stats.get('last_rule_id', ''), 100)}",
            f"last_blocker：{safe_text(getattr(s, 'hook_last_blocker', '') or stats.get('last_blocker', ''), 220) or '无'}",
            f"digest：{safe_text(getattr(s, 'hook_export_digest', ''), 32) or 'pending'}",
            "",
            "边界：",
            "- HookBus 只校验请求/事件，不执行命令。",
            "- Provider、工具、长期记忆、审计、回滚仍只能由 Runtime / TiangongWangguan 管控。",
            "- A5 allowed、run_terminal 早于 assistant_final、缺安全标记的请求会被确定性阻断。",
            "",
            "最近记录：",
        ]
        for rec in list(getattr(s, "hook_records", []) or [])[-20:]:
            lines.append(f"#{getattr(rec, 'seq', '')} {getattr(rec, 'stage', '')} · {getattr(rec, 'rule_id', '')} · {getattr(rec, 'verdict', '')} · {getattr(rec, 'reason', '')}")
        self._show_safe_detail("HookBus 详情", lines)

    def _show_boundary_detail(self) -> None:
        lines = [
            "FE.01 STEP25 / L6.64 安全边界：",
            "- 真实 Runtime 只通过 /chat/stream-events 连接",
            "- Agent UI 事件只用于渲染，不作为前端命令",
            "- QualityGate 行动守卫卡只允许提交请求，不直接放行",
            "- 审计/回滚卡片只读显示，前端不写审计、不应用回滚",
            "- 流式输出采用 45ms 合并与虚拟长对话渲染",
            "- HookBus 对 chat/provider/confirmation/control/event/finalize 做确定性请求守卫",
            "- 中断/停止/复位只向 Runtime 发送请求，不由前端执行",
            "- 文件传输只提交脱敏 transfer request，不在前端执行工具或写审计",
            "- 对话引导只填入输入栏，仍由用户确认发送，不替代 Planner",
            "- Provider 设置只向 Runtime /settings/provider 提交写入请求，UI 只显示 configured/digest/错误态",
            "- 不调用 Adapter",
            "- 不直接执行工具",
            "- 不裸调模型或 Provider SDK",
            "- 不写 tiangong_kernel",
            "- 不裸写长期记忆或审计",
            "- 不直接应用回滚或自我迭代合入",
            "- Mock/JSON 模式仍保持前端本地预览",
        ]
        self._show_safe_detail("FE.01 安全边界", lines)

    def _refresh_snapshot_frontend_only(self) -> None:
        try:
            refresh = getattr(self.client, "refresh_snapshot", None)
            self.snapshot = refresh() if callable(refresh) else self.client.get_snapshot()
            self._show_frontend_notice("刷新完成", "已刷新 RuntimeClient 快照；SSE 模式仅读取 /health/runtime、/metadata/product、/settings/provider 脱敏投影。")
        except Exception as exc:
            self.snapshot = RuntimeSnapshot(
                source_kind="client_error",
                runtime_status="读取失败",
                connection_status=f"刷新失败：{safe_text(exc, 80)}",
                current_task_status="DISCONNECTED",
                progress_percent=0,
                current_stage="前端快照刷新失败",
            )
            self._show_frontend_notice("刷新失败", f"前端快照刷新失败：{safe_text(exc, 180)}")
        self.show_page(self.current_page)

    def _export_snapshot_frontend_only(self) -> None:
        export_path = Path(__file__).resolve().parents[1] / "reports" / "frontend_snapshot_export.json"
        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_text(json.dumps(self.snapshot.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        self._show_frontend_notice("导出完成", f"已导出前端快照：{export_path.name}。未写入后端内核。")

    # -------------------------------------------------------------- actions
    def _select_model_from_listbox(self, box: tk.Listbox) -> None:
        selection = box.curselection()
        if not selection:
            return
        raw = safe_text(box.get(selection[0]), 240)
        parts = [part.strip() for part in raw.split("·")]
        if len(parts) >= 2:
            self.api_provider_var.set(parts[0])
            self.main_model_var.set(parts[1])
            self.settings_status_var.set(f"已选择模型：{parts[0]} / {parts[1]}。仅更新前端设置表单，未调用 Provider。")

    def _save_runtime_settings_frontend_only(self) -> None:
        raw_settings = {
            "provider": self.api_provider_var.get(),
            "main_model": self.main_model_var.get(),
            "api_base_url": self.api_base_url_var.get(),
            "api_key": self.api_key_var.get(),
        }
        settings = sanitize_runtime_settings(raw_settings)
        self._sanitized_settings = settings
        submitter = getattr(self.client, "submit_provider_settings", None)
        result: Dict[str, Any]
        if callable(submitter):
            try:
                result = submitter(raw_settings) or {}
                state = safe_text(result.get("status") or result.get("provider_config_state") or "submitted", 40)
                message = safe_text(result.get("message") or "Runtime Provider 设置请求已提交。", 220)
                self.settings_status_var.set(
                    "Runtime 回执："
                    f"state={state}；provider={safe_text(result.get('provider') or settings['provider'], 40)}；"
                    f"model={safe_text(result.get('model') or settings['main_model'], 80)}；"
                    f"api_key_configured={result.get('api_key_configured', settings['api_key_configured'])}；"
                    f"key_digest={safe_text(result.get('api_key_digest') or settings['api_key_digest'] or '无', 32)}；"
                    f"base_url_configured={result.get('base_url_configured', settings['base_url_configured'])}；"
                    f"base_url_digest={safe_text(result.get('base_url_digest') or settings['base_url_digest'] or '无', 32)}；"
                    f"error={safe_text(result.get('config_error_code') or '无', 80)}；"
                    f"audit={safe_text(result.get('audit_id') or '无', 80)}。{message}"
                )
                try:
                    self.snapshot = self.client.get_snapshot()
                except Exception as exc:
                    self._last_snapshot_after_provider_save_error = safe_text(exc, 120)
            except Exception as exc:
                self.settings_status_var.set(
                    "Runtime Provider 设置提交失败："
                    f"provider={settings['provider']}；model={settings['main_model']}；"
                    f"api_key_configured={settings['api_key_configured']}；key_digest={settings['api_key_digest'] or '无'}；"
                    f"base_url_configured={settings['base_url_configured']}；base_url_digest={settings['base_url_digest'] or '无'}；"
                    f"error={safe_text(exc, 160)}。未调用 Provider，未写入前端持久层。"
                )
        else:
            self.settings_status_var.set(
                "已保存前端脱敏设置摘要："
                f"provider={settings['provider']}；model={settings['main_model']}；"
                f"api_key_configured={settings['api_key_configured']}；key_digest={settings['api_key_digest'] or '无'}；"
                f"base_url_configured={settings['base_url_configured']}；base_url_digest={settings['base_url_digest'] or '无'}。"
                "当前 RuntimeClient 不支持 /settings/provider 写入；未调用 Provider，未写入 Runtime。"
            )
        # L6.57: raw Key/Base URL are write-only inputs. Clear them after the
        # Runtime submit attempt regardless of success or failure.
        self.api_key_var.set("")
        self.api_base_url_var.set("")

    def _submit_iteration_confirmation(self, candidate_id: str, decision: str) -> None:
        submit = getattr(self.client, "submit_self_iteration_confirmation", None)
        if callable(submit):
            submit(candidate_id, decision)
        else:
            self.snapshot.submit_self_iteration_confirmation(candidate_id, decision)
        self.show_page("iteration")

    def _send_message_from_event(self, _event: tk.Event) -> str:
        self._send_message()
        return "break"

    def _insert_newline_from_event(self, event: tk.Event) -> str:
        widget = event.widget
        try:
            widget.insert("insert", "\n")
        except Exception as exc:
            self._last_input_error = safe_text(exc, 120)
        return "break"

    def _send_message(self) -> None:
        if hasattr(self, "input_text"):
            text = self.input_text.get("1.0", "end").strip()
        else:
            text = getattr(self, "input_var", tk.StringVar()).get().strip()
        if not text:
            self._show_frontend_notice("输入为空", "请输入消息；空输入不会提交到 Runtime。")
            return
        with self._stream_lock:
            if self._stream_worker is not None and self._stream_worker.is_alive():
                self._show_frontend_notice("任务进行中", "当前已有流式任务在进行；请先等待收口，或向 Runtime 发送停止请求。")
                return
        if hasattr(self, "input_text"):
            self.input_text.delete("1.0", "end")
        self.stream_status_var.set("流式状态：提交中")
        submit_stream = getattr(self.client, "submit_user_message_streaming", None)
        if not callable(submit_stream):
            self.client.submit_user_message(text)
            self.show_page("chat")
            return

        def on_snapshot(snapshot: RuntimeSnapshot) -> None:
            self.after(0, lambda snap=snapshot: self._queue_stream_snapshot(snap))

        def worker() -> None:
            try:
                snapshot = submit_stream(text, on_snapshot=on_snapshot)
                self.after(0, lambda snap=snapshot: self._queue_stream_snapshot(snap, finished=True, force=True))
            except Exception as exc:
                self.after(0, lambda err=exc: self._stream_failed(err))

        t = threading.Thread(target=worker, name="linyuanzhe-runtime-sse-stream", daemon=True)
        with self._stream_lock:
            self._stream_worker = t
        t.start()

    def _queue_stream_snapshot(self, snapshot: RuntimeSnapshot, *, finished: bool = False, force: bool = False) -> None:
        self._pending_stream_snapshot = snapshot
        self._pending_stream_finished = self._pending_stream_finished or finished
        if force or finished or self._render_scheduler.should_render(force=False):
            if self._render_after_id is not None:
                try:
                    self.after_cancel(self._render_after_id)
                except tk.TclError as exc:
                    self._last_render_cancel_error = safe_text(exc, 120)
                self._render_after_id = None
            self._flush_pending_stream_snapshot()
            return
        if self._render_after_id is None:
            self._render_after_id = self.after(45, self._flush_pending_stream_snapshot)

    def _flush_pending_stream_snapshot(self) -> None:
        snapshot = self._pending_stream_snapshot
        finished = self._pending_stream_finished
        self._pending_stream_snapshot = None
        self._pending_stream_finished = False
        self._render_after_id = None
        if snapshot is not None:
            self._render_scheduler.should_render(force=True)
            self._apply_stream_snapshot(snapshot, finished=finished)

    def _apply_stream_snapshot(self, snapshot: RuntimeSnapshot, finished: bool = False) -> None:
        self.snapshot = snapshot
        self.stream_status_var.set(
            f"流式状态：{safe_text(getattr(snapshot, 'stream_state', 'unknown'), 40)} · "
            f"seq={getattr(snapshot, 'last_event_seq', 0)} · reconnect={getattr(snapshot, 'reconnect_attempts', 0)} · "
            f"visible={getattr(snapshot, 'visible_message_count', len(snapshot.chat_messages))} · hidden={getattr(snapshot, 'hidden_message_count', 0)}"
        )
        if self.current_page == "chat":
            self.show_page("chat")
        else:
            self._render_statusbar(snapshot)
        if finished:
            with self._stream_lock:
                self._stream_worker = None

    def _stream_failed(self, exc: Exception) -> None:
        with self._stream_lock:
            self._stream_worker = None
        self.snapshot = RuntimeSnapshot(
            source_kind="client_error",
            runtime_status="流式失败",
            connection_status=f"流式线程失败：{safe_text(exc, 120)}",
            current_task_status="PARTIAL_OR_FAILED",
            progress_percent=0,
            current_stage="前端流式线程失败，未执行工具",
            stream_state="error",
        )
        self.stream_status_var.set("流式状态：error")
        self.show_page("chat")

    def _insert_guided_prompt(self, text: str) -> None:
        prompt = safe_text(text, 240)
        if not prompt:
            return
        if hasattr(self, "input_text"):
            current = self.input_text.get("1.0", "end").strip()
            next_text = (current + "\n" + prompt).strip() if current else prompt
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", next_text)
            self.input_text.focus_set()
        else:
            self.client.submit_user_message(prompt)
            self.show_page("chat")
        self.stream_status_var.set("对话引导：已填入输入栏，等待用户确认发送")

    def _select_session(self, session_id_digest: str) -> None:
        self.selected_session_id = safe_text(session_id_digest, 80)
        self.stream_status_var.set(f"任务塔台：已选中 session_digest={self.selected_session_id}")

    def _request_session_search(self) -> None:
        query = safe_text(self.session_search_var.get(), 120)
        requester = getattr(self.client, "request_session_search", None)
        if callable(requester):
            self.snapshot = requester(query)
        else:
            self.snapshot.record_session_search(query)
        self.stream_status_var.set(f"任务搜索：{query or '全部'}")
        self.show_page("sessions")

    def _request_session_resume_active(self) -> None:
        sessions = list(getattr(self.snapshot, "task_sessions", []) or [])
        target = self.selected_session_id
        if not target:
            for item in sessions:
                if getattr(item, "recoverable", False):
                    target = safe_text(getattr(item, "session_id_digest", ""), 80)
                    break
        if not target and sessions:
            target = safe_text(getattr(sessions[0], "session_id_digest", ""), 80)
        if not target:
            self._show_frontend_notice("无可恢复任务", "当前没有可恢复或可选 Session；前端不会构造本地恢复。")
            return
        self._request_session_resume(target)

    def _request_session_resume(self, session_id_digest: str) -> None:
        requester = getattr(self.client, "request_session_resume", None)
        if callable(requester):
            self.snapshot = requester(session_id_digest, "user_clicked_session_resume")
            self.stream_status_var.set(f"Session 恢复：{safe_text(getattr(self.snapshot, 'session_manager_state', 'requested'), 80)}")
            self.show_page("sessions")
            return
        self._show_frontend_notice("恢复不可用", "当前 RuntimeClient 不支持 Session 恢复请求；前端不会自行恢复工具或回滚。")

    def _show_session_detail(self, session_id_digest: str = "") -> None:
        sid = safe_text(session_id_digest or self.selected_session_id, 80)
        lines = [
            "L6.67 多任务 Session 管理器：",
            f"contract：{safe_text(getattr(self.snapshot, 'session_manager_contract', ''), 100)}",
            f"state：{safe_text(getattr(self.snapshot, 'session_manager_state', ''), 80)}",
            f"last_message：{safe_text(getattr(self.snapshot, 'session_last_message', ''), 220)}",
            "",
            "规则：",
            "- 前端只显示 Session 投影和提交 resume/search envelope。",
            "- 前端不得直接恢复工具、切换 Runtime、写长期记忆、写审计或应用回滚。",
            "- 失败恢复、等待确认、任务归档必须继续由 Runtime / TiangongWangguan 裁决。",
            "",
            "匹配任务：",
        ]
        found = False
        for item in list(getattr(self.snapshot, "task_sessions", []) or []):
            if not sid or safe_text(getattr(item, "session_id_digest", ""), 80) == sid:
                found = True
                lines.append(f"- {safe_text(getattr(item, 'title', ''), 120)} · {safe_text(getattr(item, 'status', ''), 40)} · progress={getattr(item, 'progress_percent', 0)}% · audit={safe_text(getattr(item, 'audit_id', ''), 80)} · digest={safe_text(getattr(item, 'session_id_digest', ''), 80)}")
        if not found:
            lines.append("- 未找到匹配 Session。")
        self._show_safe_detail("任务 Session 详情", lines)

    def _show_installer_detail(self) -> None:
        s = self.snapshot
        manifest = getattr(s, "installer_manifest", None)
        lines = [
            "L6.69 安装器 / Windows 打包器 RC 前置结构：",
            f"contract：{safe_text(getattr(s, 'installer_rc_contract', ''), 100)}",
            f"stage：{safe_text(getattr(s, 'installer_stage', ''), 80)}",
            f"version：{safe_text(getattr(manifest, 'version_label', ''), 100)}",
            f"developer：{safe_text(getattr(manifest, 'unique_developer', ''), 80)}",
            f"angel：{safe_text(getattr(manifest, 'angel_investor', ''), 80)}",
            f"update_channel：{safe_text(getattr(s, 'update_channel', ''), 80)}",
            f"startup_self_check_state：{safe_text(getattr(s, 'startup_self_check_state', ''), 80)}",
            f"rollback_ready：{getattr(manifest, 'rollback_ready', False)}",
            f"offline_repair_available：{getattr(manifest, 'offline_repair_available', False)}",
            "",
            "版本槽：",
        ]
        for slot in list(getattr(s, "version_slots", []) or [])[:12]:
            lines.append(f"- {safe_text(getattr(slot, 'slot_name', ''), 60)} · {safe_text(getattr(slot, 'state', ''), 40)} · {safe_text(getattr(slot, 'version_label', ''), 80)} · digest={safe_text(getattr(slot, 'path_digest', ''), 80)}")
        lines.append("")
        lines.append("启动自检：")
        for check in list(getattr(s, "startup_self_checks", []) or [])[:20]:
            lines.append(f"- {safe_text(getattr(check, 'check_id', ''), 60)} · {safe_text(getattr(check, 'status', ''), 40)} · {safe_text(getattr(check, 'message', ''), 180)}")
        lines.append("")
        lines.append("边界：这是安装器/打包器/更新器/回滚器的前置结构展示。前端不可生成安装包、不可应用更新、不可恢复回滚槽、不可上传崩溃报告、不可修改 Runtime 核心文件；L6.69 只允许 dry-run 报告。")
        self._show_safe_detail("安装器 RC 详情", lines)

    def _request_file_transfer_from_dialog(self) -> None:
        try:
            path = filedialog.askopenfilename(title="选择要交给临渊者的文件")
        except tk.TclError as exc:
            self._show_frontend_notice("文件选择不可用", f"当前环境无法打开文件选择器：{safe_text(exc, 160)}")
            return
        if not path:
            return
        requester = getattr(self.client, "request_file_transfer", None)
        if not callable(requester):
            self._show_frontend_notice("文件传输不可用", "当前 RuntimeClient 不支持文件传输请求；前端不会自行读取并传输文件。")
            return
        self.snapshot = requester(path, "user_attachment")
        self.stream_status_var.set(f"文件传输：{safe_text(getattr(self.snapshot, 'file_transfer_state', 'requested'), 80)}")
        self.show_page("files")

    def _request_task_interrupt(self) -> None:
        requester = getattr(self.client, "request_task_interrupt", None)
        if callable(requester):
            self.snapshot = requester("user_clicked_interrupt_button")
            self.stream_status_var.set(f"控制状态：{safe_text(getattr(self.snapshot, 'control_state', 'interrupt_requested'), 60)}")
            self.show_page(self.current_page)
            return
        self._show_frontend_notice("中断不可用", "当前 RuntimeClient 不支持中断请求；前端不会自行杀 Runtime 或工具。")


    def _request_file_authorization_from_dialog(self, mode: str = "read") -> None:
        try:
            path = filedialog.askopenfilename(title="选择需要授权给 Agent Workspace 的文件")
        except tk.TclError as exc:
            self._show_frontend_notice("文件授权不可用", f"当前环境无法打开文件选择器：{safe_text(exc, 160)}")
            return
        if not path:
            return
        requester = getattr(self.client, "request_file_authorization", None)
        if not callable(requester):
            self._show_frontend_notice("文件授权不可用", "当前 RuntimeClient 不支持工作区文件授权请求；前端不会自行创建工作区或复制文件。")
            return
        self.snapshot = requester(path, mode, "user_selected_file", "user_selected_workspace_authorization")
        self.stream_status_var.set(f"工作区授权：{safe_text(getattr(self.snapshot, 'workspace_state', 'requested'), 80)}")
        self.show_page("workspace")

    def _show_workspace_detail(self) -> None:
        s = self.snapshot
        lines = [
            "L6.65 Agent Workspace / 沙箱与文件授权边界：",
            f"contract：{safe_text(getattr(s, 'workspace_contract', ''), 100)}",
            f"state：{safe_text(getattr(s, 'workspace_state', ''), 80)}",
            f"last_message：{safe_text(getattr(s, 'workspace_last_message', ''), 220)}",
            "",
            "规则：",
            "- 前端只显示工作区策略和提交授权 envelope。",
            "- 前端不得创建工作区、修改 ACL、复制文件字节、显示原始路径或下载 token。",
            "- 写入授权必须继续经 Runtime / QualityGate / TiangongWangguan 裁决。",
            "- 下载只显示中转回执与 token digest，不显示原始 token。",
            "",
            "最近授权：",
        ]
        for rec in list(getattr(s, "file_authorization_records", []) or [])[-20:]:
            lines.append(f"- {getattr(rec, 'file_name', '')} · {getattr(rec, 'mode', '')} · {getattr(rec, 'status', '')} · path_digest={getattr(rec, 'path_digest', '')} · audit={getattr(rec, 'audit_id', '')}")
        self._show_safe_detail("工作区详情", lines)

    def _show_file_transfer_detail(self) -> None:
        s = self.snapshot
        lines = [
            "L6.64/L6.65 文件传输与工作区边界：",
            f"contract：{safe_text(getattr(s, 'file_transfer_contract', ''), 100)}",
            f"state：{safe_text(getattr(s, 'file_transfer_state', ''), 80)}",
            f"last_message：{safe_text(getattr(s, 'file_transfer_last_message', ''), 220)}",
            "",
            "规则：",
            "- 前端只选择文件并生成脱敏 transfer request。",
            "- 报告与日志只保留文件名、大小、摘要和 Runtime 回执。",
            "- 原始路径、文件正文、Provider 凭证、审计写入和工具调用均禁止出现在前端层。",
            "- 真实读取、落盘、转存、下载中转必须由 Runtime / TiangongWangguan / QualityGate 管控。",
            "",
            "最近记录：",
        ]
        for rec in list(getattr(s, "file_transfer_records", []) or [])[-20:]:
            lines.append(f"- {getattr(rec, 'file_name', '')} · {getattr(rec, 'status', '')} · digest={getattr(rec, 'sha256_digest', '')} · audit={getattr(rec, 'audit_id', '')}")
        self._show_safe_detail("文件传输详情", lines)


    def _request_connector_registration(self) -> None:
        name = safe_text(getattr(self, "connector_name_var", tk.StringVar(value="未命名连接器")).get(), 120)
        kind = safe_text(getattr(self, "connector_kind_var", tk.StringVar(value="mcp_server")).get(), 80)
        requester = getattr(self.client, "request_connector_registration", None)
        if not callable(requester):
            self._show_frontend_notice("连接器注册不可用", "当前 RuntimeClient 不支持连接器注册请求；前端不会自行安装 MCP 或执行连接器。")
            return
        self.snapshot = requester(name, kind, ["read_public_metadata"], ["registry_review"])
        self.stream_status_var.set(f"连接器注册：{safe_text(getattr(self.snapshot, 'connector_registry_state', 'requested'), 80)}")
        self.show_page("connectors")

    def _show_connector_detail(self) -> None:
        s = self.snapshot
        lines = [
            "L6.66 MCP / 连接器注册表前置治理：",
            f"contract：{safe_text(getattr(s, 'connector_registry_contract', ''), 100)}",
            f"state：{safe_text(getattr(s, 'connector_registry_state', ''), 80)}",
            f"last_message：{safe_text(getattr(s, 'connector_last_message', ''), 220)}",
            "",
            "规则：",
            "- 前端只显示注册表投影和提交注册 envelope。",
            "- 前端不得安装 MCP server、执行连接器、存储连接器密钥、直连外部 endpoint。",
            "- 连接器默认 disabled/read_only；启用、隔离、执行必须经 Runtime / QualityGate / Agent Workspace。",
            "- 开放市场一键安装在 RC 前置包中禁用。",
            "",
            "最近注册：",
        ]
        for rec in list(getattr(s, "connector_registration_records", []) or [])[-20:]:
            lines.append(f"- {getattr(rec, 'display_name', '')} · {getattr(rec, 'kind', '')} · {getattr(rec, 'status', '')} · manifest_digest={getattr(rec, 'manifest_digest', '')} · audit={getattr(rec, 'audit_id', '')}")
        self._show_safe_detail("连接器详情", lines)

    def _request_task_stop(self) -> None:
        requester = getattr(self.client, "request_task_stop", None)
        if callable(requester):
            self.snapshot = requester("user_clicked_stop_button")
            self.stream_status_var.set(f"控制状态：{safe_text(getattr(self.snapshot, 'control_state', 'stop_requested'), 60)}")
            self.show_page(self.current_page)
            return
        self._show_frontend_notice("停止不可用", "当前 RuntimeClient 不支持停止请求；前端不会自行停止工具。")

    def _request_task_reset(self) -> None:
        requester = getattr(self.client, "request_task_reset", None)
        if callable(requester):
            self.snapshot = requester("user_clicked_reset_button")
            self.stream_status_var.set(f"控制状态：{safe_text(getattr(self.snapshot, 'control_state', 'reset_requested'), 60)}")
            self.show_page(self.current_page)
            return
        self._show_frontend_notice("复位不可用", "当前 RuntimeClient 不支持复位请求；前端不会自行复位 Runtime。")

    def _request_runtime_reconnect(self) -> None:
        self._refresh_snapshot_frontend_only()
        self.stream_status_var.set("流式状态：已发起 Runtime health 重连刷新")

    def _submit_action_guard_decision(self, ticket_id: str, decision: str) -> None:
        if not ticket_id:
            self._show_frontend_notice("确认请求缺少票据", "缺少 ticket_id，前端不会构造本地放行。")
            return
        self.client.submit_confirmation(ticket_id, decision)
        self.show_page("execution")

    def _submit_confirmation(self, ticket_id: str, decision: str) -> None:
        self.client.submit_confirmation(ticket_id, decision)
        self.show_page("execution")

    def _new_task_frontend_only(self) -> None:
        self.client.submit_user_message("新建任务：FE.01 前端占位动作，不触发真实执行。")
        self.show_page("chat")

    def _import_plan_frontend_only(self) -> None:
        self.client.submit_user_message("导入计划：FE.01 前端占位动作，仅验证入口，不读取真实计划。")
        self.show_page("chat")
