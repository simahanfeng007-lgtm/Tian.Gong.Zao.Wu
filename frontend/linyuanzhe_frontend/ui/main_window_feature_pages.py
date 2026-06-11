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
from linyuanzhe_frontend.contracts.model_settings import (
    DEFAULT_MODEL_CATALOG, MODEL_CUSTOM_SENTINEL, PROVIDER_OPTIONS,
    default_base_url_for_provider, default_model_for_provider, effective_model_name,
    filter_model_catalog, model_values_for_provider, normalize_provider_value,
    provider_allows_custom_model, provider_display_name, sanitize_runtime_settings,
)
from linyuanzhe_frontend.contracts.provider_settings import provider_readiness_from_public_projection
from linyuanzhe_frontend.contracts.work_modes import work_mode_value
from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot, StepSummary, digest_text, safe_chat_text, safe_path_setting_value, safe_text
from linyuanzhe_frontend.version_info import PROVIDER_CONFIG_SCHEMA_VERSION
from .theme import COLORS, DIMENS, FONTS, STATUS_COLORS, THEME_PROFILES, UI_FONT_FAMILIES, CODE_FONT_FAMILIES
from .localization import ui_text, permission_mode_label, permission_mode_value, host_access_scope_label, host_access_scope_value, connector_kind_label
from .widgets import Card, Chip, MetricRow, StepItem, LabeledValue, StatusPill, Tooltip, make_button, make_hint, make_readonly_banner, make_section_title, make_vertical_scrollbar


class FeaturePagesMixin:
    def _build_sessions_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(root, "任务", "多任务投影、搜索、恢复请求、等待确认、失败归档；恢复按钮只向运行时提交请求，不由前端直接恢复工具。").grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

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
            ("阻断", stats.get("已阻断", 0), COLORS["danger"] if int(stats.get("已阻断", 0) or 0) else COLORS["success"]),
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
        make_hint(metric_body, f"契约={safe_text(getattr(s, 'session_manager_contract', ''), 100)} · {safe_text(getattr(s, 'session_last_message', ''), 180)}", bg=COLORS["bg_card"], wraplength=980).grid(row=1, column=0, columnspan=len(metric_items), sticky="ew", pady=(10, 0))

        sessions_card = Card(body, "任务会话 列表")
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
            msg = f"阶段={safe_text(getattr(item, 'current_stage', ''), 100)} · 摘要指纹={safe_text(getattr(item, 'session_id_digest', ''), 40)} · 审计={safe_text(getattr(item, 'audit_id', ''), 40) or '无'}"
            tk.Label(row, text=msg, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=720, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 6))
            buttons = tk.Frame(row, bg=COLORS["bg_card_2"])
            buttons.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 8))
            sid = safe_text(getattr(item, "session_id_digest", ""), 80)
            tk.Button(buttons, text="选中", command=lambda x=sid: self._select_session(x), bg=COLORS["bg_card"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=4).pack(side="left", padx=(0, 6))
            if getattr(item, "recoverable", False):
                tk.Button(buttons, text="请求运行时恢复", command=lambda x=sid: self._request_session_resume(x), bg=COLORS["warning"], fg="#FFFFFF", relief="flat", padx=10, pady=4).pack(side="left", padx=(0, 6))
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
        hints = ["F5 刷新", "Ctrl+R 请求运行时恢复", "Ctrl+F 打开任务页", "Ctrl+. 中断当前任务"]
        for i, hint in enumerate(hints, start=1):
            tk.Label(frm, text=f"• {hint}", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=i, column=0, columnspan=2, sticky="w", pady=(8 if i == 1 else 3, 0))

        boundary = Card(side, "任务边界")
        boundary.grid(row=1, column=0, sticky="ew")
        rules = ["显示运行时任务会话投影", "恢复/搜索只提交请求 envelope", "点恢复后会有弹窗和状态栏回执", "不直接恢复工具或运行命令", "失败恢复仍由运行时 / 天工网关裁决"]
        for idx, rule in enumerate(rules, start=1):
            tk.Label(boundary, text=f"✓ {rule}", bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["small"]).grid(row=idx, column=0, sticky="w", padx=14, pady=(8 if idx == 1 else 4, 0))
        tk.Button(boundary, text="任务详情", command=self._show_session_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=len(rules) + 1, column=0, sticky="w", padx=14, pady=(12, 14))

    def _build_history_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(root, "历史", "本地对话记录、只读回放、全文检索与导出。历史只保存在 workspace/chat_history；不写运行时记忆或审计。") .grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(1, weight=1)

        query = safe_text(self.history_search_var.get(), 120)
        try:
            records = self.history_store.list_records(query, limit=160)
        except Exception as exc:
            records = []
            self._record_ui_warning("history_page_list", exc, 160)

        metrics = Card(body, "本地历史指标")
        metrics.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        metric_body = tk.Frame(metrics, bg=COLORS["bg_card"])
        metric_body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        for col in range(4):
            metric_body.grid_columnconfigure(col, weight=1)
        total_messages = sum(int(getattr(item, "message_count", 0) or 0) for item in records)
        metric_items = [
            ("记录", len(records), COLORS["accent"]),
            ("消息", total_messages, COLORS["success"]),
            ("目录", "workspace/chat_history", COLORS["text_main"]),
            ("模式", "只读回放", COLORS["warning"]),
        ]
        for idx, (label, value, color) in enumerate(metric_items):
            box = tk.Frame(metric_body, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            box.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 8, 0))
            tk.Label(box, text=str(value), bg=COLORS["bg_card_2"], fg=color, font=FONTS["number"] if isinstance(value, int) else FONTS["body_bold"]).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(box, text=label, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(anchor="w", padx=10, pady=(0, 8))
        make_hint(metric_body, "历史记录只用于桌面端回放/导出。点击加载会进入聊天区只读模式，不会继续对话、不会写入记忆、不会触发工具。", bg=COLORS["bg_card"], wraplength=980).grid(row=1, column=0, columnspan=4, sticky="ew", pady=(10, 0))

        history_card = Card(body, "历史列表")
        history_card.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        list_body = tk.Frame(history_card, bg=COLORS["bg_card"])
        list_body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 14))
        list_body.grid_columnconfigure(0, weight=1)
        if not records:
            make_hint(list_body, "暂无本地历史，或当前搜索无命中。", bg=COLORS["bg_card"]).grid(row=0, column=0, sticky="ew", pady=12)
        last_bucket = ""
        row_index = 0
        for item in records[:80]:
            bucket = safe_text(getattr(item, "date_bucket", "更早"), 20)
            if bucket != last_bucket:
                row_index += 1
                tk.Label(list_body, text=bucket, bg=COLORS["bg_card"], fg=COLORS["accent_line"], font=FONTS["small_bold"], anchor="w").grid(row=row_index, column=0, sticky="ew", pady=(10 if row_index > 1 else 0, 6))
                last_bucket = bucket
            row_index += 1
            row = tk.Frame(list_body, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            row.grid(row=row_index, column=0, sticky="ew", pady=(0, 8))
            row.grid_columnconfigure(0, weight=1)
            title = safe_text(getattr(item, "title", "未命名对话"), 80)
            if query:
                title_display = title.replace(query, f"【{query}】")
            else:
                title_display = title
            tk.Label(row, text=title_display, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["body_bold"], anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
            meta = f"{safe_text(getattr(item, 'updated_at', ''), 24)} · {getattr(item, 'message_count', 0)} 条消息 · {safe_text(getattr(item, 'preview', ''), 80)}"
            tk.Label(row, text=meta, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=760, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 6))
            buttons = tk.Frame(row, bg=COLORS["bg_card_2"])
            buttons.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 8))
            sid = safe_text(getattr(item, "session_id", ""), 120)
            tk.Button(buttons, text="选中", command=lambda x=sid: self._select_local_history(x), bg=COLORS["bg_card"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=4).pack(side="left", padx=(0, 6))
            tk.Button(buttons, text="只读加载", command=lambda x=sid: self._load_local_history_readonly(x), bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=10, pady=4).pack(side="left", padx=(0, 6))
            tk.Button(buttons, text="导出 MD", command=lambda x=sid: (self._select_local_history(x), self._export_selected_history("md")), bg=COLORS["bg_card"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=4).pack(side="left")

        side = tk.Frame(body, bg=COLORS["bg_root"], width=360)
        side.grid(row=1, column=1, sticky="nsew")
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)
        search = Card(side, "搜索 / 导出")
        search.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        frm = tk.Frame(search, bg=COLORS["bg_card"])
        frm.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14))
        frm.grid_columnconfigure(0, weight=1)
        tk.Entry(frm, textvariable=self.history_search_var, bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat", font=FONTS["body"]).grid(row=0, column=0, sticky="ew", ipady=6)
        tk.Button(frm, text="全文检索", command=self._request_history_search, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=12, pady=6).grid(row=0, column=1, padx=(8, 0))
        tk.Button(frm, text="导出 Markdown", command=lambda: self._export_selected_history("md"), bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=12, pady=6).grid(row=1, column=0, sticky="ew", pady=(10, 0))
        tk.Button(frm, text="导出纯文本", command=lambda: self._export_selected_history("txt"), bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=12, pady=6).grid(row=2, column=0, sticky="ew", pady=(8, 0))
        tk.Button(frm, text="导出 JSON", command=lambda: self._export_selected_history("json"), bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=12, pady=6).grid(row=3, column=0, sticky="ew", pady=(8, 0))
        tk.Button(frm, text="清除本地数据", command=self._clear_local_data_frontend_only, bg=COLORS["danger"], fg="#FFFFFF", relief="flat", padx=12, pady=6).grid(row=4, column=0, sticky="ew", pady=(12, 0))

        boundary = Card(side, "历史边界")
        boundary.grid(row=1, column=0, sticky="ew")
        rules = ["自动保存到 workspace/chat_history", "只读加载不触发模型和工具", "导出支持 Markdown / TXT / JSON", "清除本地数据需二次确认", "不删除运行时审计和长期记忆"]
        for idx, rule in enumerate(rules, start=1):
            tk.Label(boundary, text=f"✓ {rule}", bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["small"]).grid(row=idx, column=0, sticky="w", padx=14, pady=(8 if idx == 1 else 4, 0))

    def _build_observability_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(
            root,
            "运行观测台",
            "L6.62 只读运行观测：展示运行时流式事件、智能体界面事件、质量门、工具、错误、预算与收口顺序，不产生执行权限。",
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(1, weight=1)

        stats = dict(getattr(s, "trace_stats", {}) or {})
        metrics = Card(body, "轨迹指标")
        metrics.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        self._populate_observability_metrics(metrics, s, stats)

        timeline = Card(body, "运行轨迹时间线")
        timeline.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        self._populate_trace_table(timeline, list(getattr(s, "trace_records", []) or []))

        side = tk.Frame(body, bg=COLORS["bg_root"], width=360)
        side.grid(row=1, column=1, sticky="nsew")
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)

        closeout = Card(side, "流式收口")
        closeout.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        LabeledValue(closeout, "最终回复→运行收口", "有效" if getattr(s, "trace_terminal_order_valid", True) else "异常", COLORS["success"] if getattr(s, "trace_terminal_order_valid", True) else COLORS["danger"]).grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 4))
        LabeledValue(closeout, "最近序号", str(stats.get("last_seq", getattr(s, "last_event_seq", 0)))).grid(row=2, column=0, sticky="ew", padx=14, pady=4)
        LabeledValue(closeout, "流式状态", safe_text(getattr(s, "stream_state", "idle"), 60)).grid(row=3, column=0, sticky="ew", padx=14, pady=(4, 14))

        runtime = Card(side, "运行状态")
        runtime.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        LabeledValue(runtime, "运行时", s.runtime_status).grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 4))
        LabeledValue(runtime, "预算", f"{s.budget_pool} / {s.budget_used_ratio}").grid(row=2, column=0, sticky="ew", padx=14, pady=4)
        LabeledValue(runtime, "质量门", s.gate_status).grid(row=3, column=0, sticky="ew", padx=14, pady=4)
        LabeledValue(runtime, "延迟", f"{s.latency_ms}ms").grid(row=4, column=0, sticky="ew", padx=14, pady=(4, 14))

        boundary = Card(side, "观测边界")
        boundary.grid(row=2, column=0, sticky="ew")
        rules = [
            "只读显示运行时公共投影 / 流式事件",
            "不裸调模型服务或工具",
            "不写长期记忆、审计或回滚",
            "运行/任务只显示摘要指纹",
            "密钥、路径、端点自动脱敏",
        ]
        for idx, rule in enumerate(rules, start=1):
            tk.Label(boundary, text=f"✓ {rule}", bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["small"]).grid(row=idx, column=0, sticky="w", padx=14, pady=(8 if idx == 1 else 4, 0))
        tk.Button(boundary, text="查看轨迹详情", command=self._show_observability_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=len(rules) + 1, column=0, sticky="w", padx=14, pady=(12, 14))

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
            ("待确认", stats.get("待生成_confirmations", s.待生成_confirmation_count), COLORS["warning"]),
        ]
        for idx, (label, value, color) in enumerate(items):
            box = tk.Frame(body, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            box.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 8, 0))
            tk.Label(box, text=str(value), bg=COLORS["bg_card_2"], fg=color, font=FONTS["number"]).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(box, text=label, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(anchor="w", padx=10, pady=(0, 8))
        make_hint(body, f"契约={safe_text(getattr(s, 'observability_contract', ''), 90)} · 导出摘要指纹={safe_text(getattr(s, 'trace_export_digest', ''), 32) or '待生成'}", bg=COLORS["bg_card"], wraplength=980).grid(row=1, column=0, columnspan=6, sticky="ew", pady=(10, 0))

    def _populate_trace_table(self, card: Card, records: List[Any]) -> None:
        table = tk.Frame(card, bg=COLORS["bg_card"])
        table.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 14))
        headers = ["序号", "类别", "事件", "阶段/状态", "引用", "消息"]
        widths = [6, 12, 18, 22, 22, 44]
        for col, (header, width) in enumerate(zip(headers, widths)):
            table.grid_columnconfigure(col, weight=1 if col in (3, 5) else 0)
            tk.Label(table, text=header, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], width=width, anchor="w", padx=6, pady=6).grid(row=0, column=col, sticky="ew", padx=(0, 1), pady=(0, 1))
        if not records:
            make_hint(table, "暂无轨迹记录。真实运行时流式事件到达后显示。", bg=COLORS["bg_card"]).grid(row=1, column=0, columnspan=len(headers), sticky="w", pady=12)
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

    def _build_hooks_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(
            root,
            "规则总线确定性规则层",
            "L6.63：只读展示请求守卫、事件守卫、A5 阻断、流式收口检查与规则记录；不产生前端执行权限。",
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(1, weight=1)

        stats = dict(getattr(s, "hook_stats", {}) or {})
        metrics = Card(body, "规则指标")
        metrics.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        self._populate_hook_metrics(metrics, s, stats)

        table = Card(body, "规则决策记录")
        table.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        self._populate_hook_table(table, list(getattr(s, "hook_records", []) or []))

        side = tk.Frame(body, bg=COLORS["bg_root"], width=380)
        side.grid(row=1, column=1, sticky="nsew")
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)

        boundary = Card(side, "确定性边界")
        boundary.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        rules = [
            "规则总线 仅校验请求/事件，不执行命令",
            "前端不可调用 模型服务 SDK 或工具",
            "前端不可写长期记忆、审计、回滚",
            "A5 必须 已阻断 或 requires_confirmation",
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
        make_hint(blocker, last_blocker or "暂无 规则总线 阻断；如果真实 运行时 返回 A5 allowed 或 run_terminal 顺序错误，会在这里显示。", bg=COLORS["bg_card"], wraplength=330).grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 14))

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
            ("规则总数", stats.get("total_hooks", len(getattr(s, "hook_records", []) or [])), COLORS["accent"]),
            ("允许", stats.get("allow_count", 0), COLORS["success"]),
            ("警告", stats.get("warn_count", 0), COLORS["warning"]),
            ("阻断", stats.get("block_count", 0), COLORS["danger"] if int(stats.get("block_count", 0) or 0) else COLORS["success"]),
            ("最后", safe_text(stats.get("last_verdict", "无"), 16), COLORS["text_main"]),
        ]
        for idx, (label, value, color) in enumerate(items):
            box = tk.Frame(body, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            box.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 8, 0))
            tk.Label(box, text=str(value), bg=COLORS["bg_card_2"], fg=color, font=FONTS["number"]).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(box, text=label, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(anchor="w", padx=10, pady=(0, 8))
        make_hint(body, f"契约={safe_text(getattr(s, 'hook_bus_contract', ''), 90)} · 摘要指纹={safe_text(getattr(s, 'hook_export_digest', ''), 32) or '待生成'}", bg=COLORS["bg_card"], wraplength=980).grid(row=1, column=0, columnspan=5, sticky="ew", pady=(10, 0))

    def _populate_hook_table(self, card: Card, records: List[Any]) -> None:
        table = tk.Frame(card, bg=COLORS["bg_card"])
        table.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 14))
        headers = ["序号", "阶段", "规则", "裁决", "事件", "原因"]
        widths = [6, 22, 24, 10, 18, 48]
        for col, (header, width) in enumerate(zip(headers, widths)):
            table.grid_columnconfigure(col, weight=1 if col in (1, 2, 5) else 0)
            tk.Label(table, text=header, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], width=width, anchor="w", padx=6, pady=6).grid(row=0, column=col, sticky="ew", padx=(0, 1), pady=(0, 1))
        if not records:
            make_hint(table, "暂无规则记录。流式事件 / 设置 / 确认 / 控制请求进入后显示。", bg=COLORS["bg_card"]).grid(row=1, column=0, columnspan=len(headers), sticky="w", pady=12)
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
        """Compact memory cockpit.

        STEP31E removes the large empty memory surface. The page now shows one
        dense summary band, five memory levels, recall/forget indicators and
        recent sanitized chat snippets. It remains 公共投影-only.
        """
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(root, "记忆", "五层记忆、召回、遗忘与经验升级的紧凑投影。只显示 sanitized summary / digest / evidence_ref。") .grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(2, weight=1)

        summary = Card(body, "记忆摘要 / 召回快照")
        summary.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        summary.grid_columnconfigure(0, weight=1)
        make_hint(summary, s.memory_sanitized_summary or "暂无 运行时 记忆摘要；等待 公共投影 回填。", bg=COLORS["bg_card"], wraplength=1120).grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 8))
        meta = tk.Frame(summary, bg=COLORS["bg_card"])
        meta.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))
        for col in range(4):
            meta.grid_columnconfigure(col, weight=1)
        LabeledValue(meta, "摘要指纹", s.memory_digest or "无").grid(row=0, column=0, sticky="ew", padx=(0, 8))
        LabeledValue(meta, "证据引用", s.memory_evidence_ref or "无").grid(row=0, column=1, sticky="ew", padx=(0, 8))
        LabeledValue(meta, "模式", getattr(s, "memory_mode", "frontend_no_direct_write")).grid(row=0, column=2, sticky="ew", padx=(0, 8))
        LabeledValue(meta, "可见消息", str(getattr(s, "visible_message_count", len(getattr(s, "chat_messages", []) or [])))).grid(row=0, column=3, sticky="ew")

        levels = Card(body, "五层记忆状态")
        levels.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        level_rows = [
            ("L1 瞬时", "当前对话窗口内临时上下文", "只读投影"),
            ("L2 模糊", "候选经验与弱信号", "等待强成功信号"),
            ("L3 经验", "可转 Skill / Tool 的成功路径", "由记忆认知引擎升级"),
            ("L4 稳定", "长期偏好、稳定事实、项目基线", "脱敏摘要展示"),
            ("L5 规则", "长期规则与硬边界", "只显示规则摘要"),
        ]
        table = tk.Frame(levels, bg=COLORS["bg_card"])
        table.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        table.grid_columnconfigure(1, weight=1)
        for idx, (name, desc, state) in enumerate(level_rows):
            bg = COLORS["bg_card_2"] if idx % 2 == 0 else COLORS["bg_card"]
            tk.Label(table, text=name, bg=bg, fg=COLORS["accent"], font=FONTS["body_bold"], width=12, anchor="w", padx=8, pady=7).grid(row=idx, column=0, sticky="ew", pady=(0, 2))
            tk.Label(table, text=desc, bg=bg, fg=COLORS["text_main"], font=FONTS["body"], anchor="w", padx=8, pady=7).grid(row=idx, column=1, sticky="ew", pady=(0, 2))
            tk.Label(table, text=state, bg=bg, fg=COLORS["text_sub"], font=FONTS["small"], anchor="e", padx=8, pady=7).grid(row=idx, column=2, sticky="ew", pady=(0, 2))

        signals = Card(body, "召回 / 遗忘 / 升级信号")
        signals.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        signal_rows = [
            ("召回状态", "等待运行时召回投影" if not s.memory_digest else "摘要可用"),
            ("遗忘状态", "前端不触发遗忘；只显示回执"),
            ("L2→L3", "由记忆系统认知引擎裁决"),
            ("写入权限", "禁止前端直接写长期记忆"),
            ("证据", s.memory_evidence_ref or "无"),
        ]
        for idx, (label, value) in enumerate(signal_rows, start=1):
            LabeledValue(signals, label, safe_text(value, 96)).grid(row=idx, column=0, sticky="ew", padx=14, pady=(7 if idx == 1 else 4, 0))

        recent = Card(body, "最近脱敏对话 / 记忆候选")
        recent.grid(row=2, column=0, columnspan=2, sticky="nsew")
        recent.grid_columnconfigure(0, weight=1)
        messages = list(getattr(s, "chat_messages", []) or [])[-8:]
        if not messages:
            make_hint(recent, "暂无可显示的脱敏对话摘要。", bg=COLORS["bg_card"], wraplength=1100).grid(row=1, column=0, sticky="ew", padx=14, pady=12)
        for idx, msg in enumerate(messages, start=1):
            text = f"{safe_text(getattr(msg, 'label', ''), 24)}：{safe_text(getattr(msg, 'text', ''), 180)}"
            tk.Label(recent, text=text, bg=COLORS["bg_card_2"] if idx % 2 else COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=1120, justify="left", anchor="w", padx=10, pady=6).grid(row=idx, column=0, sticky="ew", padx=14, pady=(6 if idx == 1 else 2, 0))
        make_hint(recent, "边界：此页只读展示 公共投影，不展示原始记忆正文、不展示隐私原文、不写记忆、不写审计、不触发回滚。", bg=COLORS["bg_card"], wraplength=1120).grid(row=max(2, len(messages) + 1), column=0, sticky="ew", padx=14, pady=(10, 14))

    def _build_iteration_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(root, "自我迭代区", "展示由用户沟通、失败复盘、学习缺口生成的迭代候选；确认后仍走规划器 / 执行脊柱 / 质量门。") .grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
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
            if item.status == "待生成_user_confirmation":
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
            f"待确认：{projection.待生成_count}",
            f"更新时间：{projection.last_updated}",
            "用户确认后只生成票据",
            "真实更新仍走质量门",
            "必须有回滚点",
        ]
        for idx, rule in enumerate(rules, start=1):
            tk.Label(status, text=f"✓ {rule}", bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["body"]).grid(row=idx, column=0, sticky="w", padx=14, pady=(8 if idx == 1 else 4, 0))

    def _build_four_paths_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        self._page_header(root, "系统", "执行、记忆、情志、生命周期与数据更新社区入口；首页不展示更新按钮，避免误触。") .grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
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

        dataup = Card(body, "数据更新社区安全更新")
        dataup.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        dataup_body = tk.Frame(dataup, bg=COLORS["bg_card"])
        dataup_body.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14))
        dataup_body.grid_columnconfigure(0, weight=1)
        make_hint(
            dataup_body,
            "更新源：Gitee 主源 + GitHub 备源。点击一键安全更新时，前端只启动独立数据更新器；更新器负责 清单校验、路径白名单、回滚点、自检和失败回滚。不会覆盖 模型服务配置、密钥、记忆、日志、审计私密数据或工作区。",
            bg=COLORS["bg_card"],
            wraplength=980,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))
        source_text = (
            "Gitee：https://gitee.com/yu-yongxiang1994/natures-craftsmanship\n"
            "GitHub：https://github.com/simahanfeng007-lgtm/Tian.Gong.Zao.Wu"
        )
        tk.Label(dataup_body, text=source_text, bg=COLORS["bg_card"], fg=COLORS["text_weak"], font=FONTS["small"], justify="left", anchor="w").grid(row=1, column=0, sticky="ew", pady=(0, 8))
        btns = tk.Frame(dataup_body, bg=COLORS["bg_card"])
        btns.grid(row=2, column=0, sticky="w", pady=(0, 8))
        tk.Button(btns, text="检查更新", command=self._dataup_check_update, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=12, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="一键安全更新", command=self._dataup_auto_update, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=12, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="选择本地数据更新包", command=self._dataup_select_package, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=12, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="更新边界", command=self._show_dataup_boundary, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=12, pady=5).pack(side="left")
        tk.Label(dataup_body, textvariable=self.dataup_status_var, bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=980, justify="left", anchor="w").grid(row=3, column=0, sticky="ew")

        digest = Card(body, "统一规划上下文")
        digest.grid(row=3, column=0, columnspan=2, sticky="ew")
        LabeledValue(digest, "context_digest", status.planner_context_digest).grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 4))
        make_hint(digest, status.hard_boundary_summary, bg=COLORS["bg_card"]).grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 14))

    def _build_installer_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(root, "安装器 / 打包器 RC 前置结构", "L6.69：安装清单、版本槽、启动自检、打包干运行、发布清单与签名策略占位；不是最终 安装程序 安装包。").grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

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
            ("回滚", "就绪" if getattr(manifest, "rollback_就绪", True) else "已阻断", COLORS["success"] if getattr(manifest, "rollback_就绪", True) else COLORS["danger"]),
            ("修复", "可用" if getattr(manifest, "offline_repair_可用", True) else "无", COLORS["warning"]),
            ("打包器", "干运行", COLORS["warning"]),
        ]
        for col in range(len(items)):
            mbody.grid_columnconfigure(col, weight=1)
        for idx, (label, value, color) in enumerate(items):
            box = tk.Frame(mbody, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            box.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 8, 0))
            tk.Label(box, text=str(value), bg=COLORS["bg_card_2"], fg=color, font=FONTS["number"]).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(box, text=label, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"]).pack(anchor="w", padx=10, pady=(0, 8))
        make_hint(mbody, f"契约={safe_text(getattr(s, 'installer_rc_contract', ''), 100)} · 通道={safe_text(getattr(s, 'update_channel', ''), 40)} · {safe_text(getattr(s, 'installer_last_message', ''), 180)}", bg=COLORS["bg_card"], wraplength=980).grid(row=1, column=0, columnspan=len(items), sticky="ew", pady=(10, 0))

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
            msg = f"路径摘要指纹={safe_text(getattr(slot, 'path_digest', ''), 40)} · 回滚={getattr(slot, 'rollback_capable', False)} · 已验证={safe_text(getattr(slot, 'last_verified', ''), 60)} · {safe_text(getattr(slot, 'message', ''), 140)}"
            tk.Label(row, text=msg, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=760, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))

        side = tk.Frame(body, bg=COLORS["bg_root"], width=380)
        side.grid(row=1, column=1, sticky="nsew")
        side.grid_propagate(False)
        checks_card = Card(side, "启动自检")
        checks_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        if not checks:
            make_hint(checks_card, "暂无启动自检记录。", bg=COLORS["bg_card"]).grid(row=1, column=0, sticky="ew", padx=14, pady=12)
        for idx, check in enumerate(checks[:8], start=1):
            status = safe_text(getattr(check, "status", "待生成"), 40)
            color = COLORS["success"] if status == "pass" else COLORS["danger"] if status in {"fail", "已阻断"} else COLORS["warning"] if status == "warn" else COLORS["text_sub"]
            LabeledValue(checks_card, safe_text(getattr(check, "name", "check"), 40), f"{status} · {safe_text(getattr(check, 'message', ''), 70)}", color).grid(row=idx, column=0, sticky="ew", padx=14, pady=(8 if idx == 1 else 4, 0))
        btn_row = tk.Frame(checks_card, bg=COLORS["bg_card"])
        btn_row.grid(row=min(len(checks), 8) + 1, column=0, sticky="w", padx=14, pady=(12, 14))
        tk.Button(btn_row, text="运行自检", command=self._run_startup_self_check, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=10, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="自检详情", command=self._show_installer_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="刷新", command=lambda: self.show_page("installer"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).pack(side="left")
        tk.Label(checks_card, textvariable=self.installer_status_var, bg=COLORS["bg_card"], fg=COLORS["text_weak"], font=FONTS["small"], wraplength=320, justify="left").grid(row=min(len(checks), 8) + 2, column=0, sticky="ew", padx=14, pady=(0, 12))

        repair_card = Card(side, "崩溃 / 离线修复")
        repair_card.grid(row=1, column=0, sticky="ew")
        for idx, crash in enumerate(crashes[:2], start=1):
            LabeledValue(repair_card, "崩溃报告", f"{safe_text(getattr(crash, 'status', ''), 40)} · count={getattr(crash, 'crash_count', 0)} · local_only={getattr(crash, 'local_only', True)}").grid(row=idx, column=0, sticky="ew", padx=14, pady=(8 if idx == 1 else 4, 0))
        base = max(1, len(crashes[:2])) + 1
        for j, action in enumerate(repairs[:4], start=base):
            LabeledValue(repair_card, safe_text(getattr(action, "title", "repair"), 40), f"{safe_text(getattr(action, 'status', ''), 40)} · no_frontend_apply={getattr(action, 'no_frontend_apply', True)}").grid(row=j, column=0, sticky="ew", padx=14, pady=(8 if j == base else 4, 0))
        tk.Button(repair_card, text="安装器边界", command=self._show_installer_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=base + len(repairs[:4]), column=0, sticky="w", padx=14, pady=(12, 14))

    def _schedule_settings_page_refresh(self, delay_ms: int = 220) -> None:
        """Debounced settings repaint for search boxes.

        L6.72.23 rebuilt the whole Settings page on every KeyRelease, which
        blocked mouse wheel scrolling and made the panel feel stuck. This keeps
        filtering responsive while avoiding rebuild storms.
        """
        after_id = getattr(self, "_settings_search_after_id", None)
        if after_id:
            try:
                self.after_cancel(after_id)
            except tk.TclError:
                pass
        def run() -> None:
            self._settings_search_after_id = None
            self._save_ui_preferences()
            if getattr(self, "current_page", "") == "settings":
                self.show_page("settings")
        try:
            self._settings_search_after_id = self.after(delay_ms, run)
        except tk.TclError:
            pass

    def _build_settings_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(root, "设置", "") .grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        identity = self._get_product_identity_public()
        provider_settings = self._get_provider_settings_public()
        readiness = self._provider_readiness_public(provider_settings)
        self._hydrate_provider_form_from_public(provider_settings)

        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        try:
            current_width = self._current_window_width()
        except Exception:
            current_width = 1280
        # 1280×800 is the baseline, but after the sidebar the Settings content
        # is too narrow for two dense columns. Keep one column until wide screens
        # so entry fields and buttons do not overflow their cards.
        columns = 2 if current_width >= 1500 else 1
        for col in range(columns):
            body.grid_columnconfigure(col, weight=1, uniform="settings_cols")

        cards = [
            self._build_model_management_card,
            self._build_soul_settings_card,
            self._build_appearance_settings_card,
            self._build_skill_panel_card,
            self._build_tool_panel_card,
            lambda parent, snap: self._build_runtime_status_card(parent, snap, readiness, identity),
            self._build_local_data_management_card,
        ]
        for idx, builder in enumerate(cards):
            row = idx if columns == 1 else idx // 2
            col = 0 if columns == 1 else idx % 2
            card = builder(body, s)
            card.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0 if col == columns - 1 else 8), pady=(0 if row == 0 else 16, 0))

    def _build_local_data_management_card(self, parent: tk.Misc, s: RuntimeSnapshot) -> Card:
        card = Card(parent, "数据管理", "本地历史、导出、恢复上次会话、托盘关闭行为。")
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14))
        body.grid_columnconfigure(0, weight=1)
        try:
            records = self.history_store.list_records(limit=999)
        except Exception:
            records = []
        make_hint(body, f"本地历史目录：workspace/chat_history；当前记录 {len(records)} 条。历史是前端本地数据，不等于长期记忆。", bg=COLORS["bg_card"], wraplength=520).grid(row=0, column=0, sticky="ew", pady=(0, 8))
        tk.Checkbutton(body, text="关闭窗口时最小化到托盘/任务栏", variable=self.minimize_to_tray_var, command=self._save_ui_preferences, bg=COLORS["bg_card"], fg=COLORS["text_main"], selectcolor=COLORS["bg_input"], activebackground=COLORS["bg_card"], activeforeground=COLORS["text_main"], font=FONTS["small"]).grid(row=1, column=0, sticky="w", pady=(2, 2))
        tk.Checkbutton(body, text="启动时恢复上次本地会话", variable=self.restore_last_session_var, command=self._save_ui_preferences, bg=COLORS["bg_card"], fg=COLORS["text_main"], selectcolor=COLORS["bg_input"], activebackground=COLORS["bg_card"], activeforeground=COLORS["text_main"], font=FONTS["small"]).grid(row=2, column=0, sticky="w", pady=(2, 2))
        tk.Checkbutton(body, text="显示任务流程", variable=self.show_task_flow_var, command=self._on_show_task_flow_changed_frontend_only, bg=COLORS["bg_card"], fg=COLORS["text_main"], selectcolor=COLORS["bg_input"], activebackground=COLORS["bg_card"], activeforeground=COLORS["text_main"], font=FONTS["small"]).grid(row=3, column=0, sticky="w", pady=(2, 2))
        make_hint(body, "关闭后仅隐藏首页任务工作台和 Codex 进度卡；Runtime/Planner/ToolMode/QualityGate/停止/重连不受影响。", bg=COLORS["bg_card"], wraplength=520).grid(row=4, column=0, sticky="ew", pady=(2, 8))
        tk.Button(body, text="保存数据设置", command=self._save_ui_preferences, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=12, pady=5).grid(row=5, column=0, sticky="w", pady=(4, 8))
        btns = tk.Frame(body, bg=COLORS["bg_card"])
        btns.grid(row=6, column=0, sticky="ew", pady=(8, 0))
        for col in range(3):
            btns.grid_columnconfigure(col, weight=1)
        for col, (label, command, bg) in enumerate([
            ("打开历史", lambda: self.show_page("history"), COLORS["accent"]),
            ("导出 MD", lambda: self._export_current_conversation("md"), COLORS["bg_card_2"]),
            ("导出 JSON", lambda: self._export_current_conversation("json"), COLORS["bg_card_2"]),
        ]):
            tk.Button(btns, text=label, command=command, bg=bg, fg="#FFFFFF" if bg == COLORS["accent"] else COLORS["text_main"], relief="flat", padx=10, pady=5).grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 6, 0))
        tk.Button(body, text="清除本地数据", command=self._clear_local_data_frontend_only, bg=COLORS["danger"], fg="#FFFFFF", relief="flat", padx=12, pady=6).grid(row=7, column=0, sticky="w", pady=(12, 0))
        make_hint(body, "托盘为可选增强：检测到 pystray/Pillow 时启用真正托盘菜单；否则关闭窗口只最小化到任务栏，不影响启动。", bg=COLORS["bg_card"], wraplength=520).grid(row=8, column=0, sticky="ew", pady=(10, 0))
        return card

    def _build_model_management_card(self, parent: tk.Misc, s: RuntimeSnapshot) -> Card:
        provider_settings = self._get_provider_settings_public()
        card = Card(parent, "模型管理", "服务商 → 所属模型列表 → 自定义模型名 / Base URL / API Key。")
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14))
        body.grid_columnconfigure(1, weight=1)
        self._populate_provider_readiness_banner(body, provider_settings, 0)
        row = 1

        tk.Label(body, text="服务商 Provider", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="w", pady=5)
        provider_box = ttk.Combobox(body, textvariable=self.api_provider_var, values=PROVIDER_OPTIONS, state="readonly")
        provider_box.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        provider_box.bind("<<ComboboxSelected>>", lambda _event: self._on_provider_changed_frontend_only(), add="+")
        row += 1

        tk.Label(body, text="模型 Model", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="w", pady=5)
        model_values = self._provider_model_values_frontend_only()
        self.provider_model_combobox = ttk.Combobox(body, textvariable=self.main_model_var, values=model_values, state="readonly")
        self.provider_model_combobox.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.provider_model_combobox.bind("<<ComboboxSelected>>", self._on_model_selected_frontend_only, add="+")
        row += 1

        tk.Label(body, text="自定义模型名", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="w", pady=5)
        self.custom_model_entry = tk.Entry(body, textvariable=self.custom_model_var, bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat")
        self.custom_model_entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5, ipady=5)
        row += 1

        tk.Label(body, text="Base URL", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="w", pady=5)
        base_entry = tk.Entry(body, textvariable=self.api_base_url_var, bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat")
        base_entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5, ipady=5)
        self.api_base_url_entry = base_entry
        base_entry.bind("<FocusOut>", lambda _event, w=base_entry: (self._normalize_base_url_entry(w), self._save_ui_preferences()), add="+")
        row += 1
        make_hint(body, "Base URL 会完整保留在设置页显示；API Key 仍只显示已配置和摘要指纹。DeepSeek 官方地址通常为 https://api.deepseek.com。", bg=COLORS["bg_card"], wraplength=520).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        row += 1

        tk.Label(body, text="API Key", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="w", pady=5)
        key_shell = tk.Frame(body, bg=COLORS["bg_card"])
        key_shell.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        key_shell.grid_columnconfigure(0, weight=1)
        self.api_key_entry = tk.Entry(key_shell, textvariable=self.api_key_var, show="" if self.api_key_visible_var.get() else "•", bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat")
        self.api_key_entry.grid(row=0, column=0, sticky="ew", ipady=5)
        self.api_key_entry.bind("<FocusOut>", lambda _event: self._mask_api_key_after_focus(), add="+")
        tk.Button(key_shell, text="👁", command=self._toggle_api_key_visibility, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=8, pady=4).grid(row=0, column=1, padx=(6, 0))
        row += 1

        tk.Label(body, text="默认模式", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="w", pady=5)
        work_mode_box = ttk.Combobox(body, textvariable=self.work_mode_var, values=["聊天", "工作"], state="readonly")
        work_mode_box.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        work_mode_box.bind("<<ComboboxSelected>>", lambda _event: self._save_ui_preferences(), add="+")
        row += 1

        tk.Label(body, text="权限模式", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="w", pady=5)
        ttk.Combobox(body, textvariable=self.tool_execution_mode_var, values=[permission_mode_label("runtime_governed"), permission_mode_label("disabled")], state="readonly").grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1

        tk.Label(body, text="电脑访问范围", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="w", pady=5)
        host_scope_box = ttk.Combobox(
            body,
            textvariable=self.host_access_scope_var,
            values=[host_access_scope_label("system_drive"), host_access_scope_label("user_home"), host_access_scope_label("project_workspace"), host_access_scope_label("custom_root")],
            state="readonly",
        )
        host_scope_box.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        host_scope_box.bind("<<ComboboxSelected>>", lambda _event: self._save_ui_preferences(), add="+")
        row += 1

        tk.Label(body, text="自定义根目录", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="w", pady=5)
        root_shell = tk.Frame(body, bg=COLORS["bg_card"])
        root_shell.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        root_shell.grid_columnconfigure(0, weight=1)
        root_entry = tk.Entry(root_shell, textvariable=self.host_access_root_var, bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat")
        root_entry.grid(row=0, column=0, sticky="ew", ipady=5)
        root_entry.bind("<FocusOut>", lambda _event: self._save_ui_preferences(), add="+")
        tk.Button(root_shell, text="选择", command=self._choose_host_access_root_frontend_only, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=8, pady=4).grid(row=0, column=1, padx=(6, 0))
        row += 1

        make_hint(
            body,
            "电脑访问范围只保存偏好；真实读取、写入、删除、审批仍由 Runtime / QualityGate 裁决。选择“自定义根目录”时可用上方路径。",
            bg=COLORS["bg_card"],
            wraplength=520,
        ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(8, 6))
        row += 1

        search_shell = tk.Frame(body, bg=COLORS["bg_card"])
        search_shell.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        search_shell.grid_columnconfigure(1, weight=1)
        tk.Label(search_shell, text="模型搜索", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=0, column=0, sticky="w")
        model_search_entry = tk.Entry(search_shell, textvariable=self.model_search_var, bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat")
        model_search_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), ipady=5)
        model_search_entry.bind("<KeyRelease>", lambda _e: self._schedule_settings_page_refresh(), add="+")
        model_search_entry.bind("<FocusOut>", lambda _e: self._save_ui_preferences(), add="+")
        tk.Button(search_shell, text="刷新", command=lambda: self._refresh_provider_model_controls_frontend_only(reset_model=False, fill_base_url=False), bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=10, pady=4).grid(row=0, column=2, padx=(8, 0))
        row += 1

        btns = tk.Frame(body, bg=COLORS["bg_card"])
        btns.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for col in range(2):
            btns.grid_columnconfigure(col, weight=1)
        model_buttons = [
            ("DeepSeek 模板", self._apply_deepseek_v4_preset_frontend_only, COLORS["bg_card_2"], COLORS["text_main"]),
            ("OpenAI 自定义", lambda: (self.api_provider_var.set("openai"), self.main_model_var.set(MODEL_CUSTOM_SENTINEL), self.custom_model_var.set(""), self._refresh_provider_model_controls_frontend_only(reset_model=False, fill_base_url=True)), COLORS["bg_card_2"], COLORS["text_main"]),
            ("保存全部设置", self._save_runtime_settings_frontend_only, COLORS["accent"], "#FFFFFF"),
            ("检查", self._test_provider_config_frontend_only, COLORS["bg_card_2"], COLORS["text_main"]),
        ]
        for idx, (label, command, bg, fg) in enumerate(model_buttons):
            tk.Button(btns, text=label, command=command, bg=bg, fg=fg, relief="flat", padx=10, pady=5).grid(row=idx // 2, column=idx % 2, sticky="ew", padx=(0 if idx % 2 == 0 else 6, 0), pady=(0 if idx < 2 else 6, 0))
        row += 1
        tk.Label(body, textvariable=self.settings_save_feedback_var, bg=COLORS["bg_card"], fg=COLORS["success"], font=FONTS["small_bold"], wraplength=520, justify="left").grid(row=row, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        row += 1
        tk.Label(body, textvariable=self.settings_status_var, bg=COLORS["bg_card"], fg=COLORS["text_weak"], font=FONTS["small"], wraplength=520, justify="left").grid(row=row, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self._refresh_provider_model_controls_frontend_only(reset_model=False, fill_base_url=False)
        return card

    def _build_soul_settings_card(self, parent: tk.Misc, s: RuntimeSnapshot) -> Card:
        card = Card(parent, "个性化 Soul / 唯一人格源", "Soul 是唯一人格与情感底色源；最多 6000 字，支持多段落。非 Soul 提示词不得影响回复风格。")
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14))
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(2, weight=1)
        tk.Label(body, text="本体名称", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=0, column=0, sticky="w", pady=5)
        name_entry = tk.Entry(body, textvariable=self.persona_name_var, bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat")
        name_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5, ipady=5)
        name_count = tk.Label(body, text="0/20", bg=COLORS["bg_card"], fg=COLORS["text_weak"], font=FONTS["small"])
        name_count.grid(row=1, column=1, sticky="w", padx=(10, 0))
        tk.Label(body, text="Soul 描述", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=2, column=0, sticky="nw", pady=(8, 5))
        soul_text_shell = tk.Frame(body, bg=COLORS["bg_input"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
        soul_text_shell.grid(row=2, column=1, sticky="nsew", padx=(10, 0), pady=(8, 5))
        soul_text_shell.grid_columnconfigure(0, weight=1)
        soul_text_shell.grid_rowconfigure(0, weight=1)
        self.persona_prompt_text = tk.Text(soul_text_shell, height=10, bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat", wrap="word", font=FONTS.get("body", FONTS["mono"]), padx=12, pady=10, undo=True)
        self.persona_prompt_text.grid(row=0, column=0, sticky="nsew")
        soul_scroll = make_vertical_scrollbar(soul_text_shell, self.persona_prompt_text.yview, variant="chat")
        soul_scroll.grid(row=0, column=1, sticky="ns")
        self.persona_prompt_text.configure(yscrollcommand=soul_scroll.set)
        self.persona_prompt_text.insert("1.0", safe_chat_text(self.persona_prompt_var.get(), 6000))

        def soul_wheel(event: tk.Event) -> str:
            try:
                delta = getattr(event, "delta", 0)
                if delta:
                    self.persona_prompt_text.yview_scroll(-1 if delta > 0 else 1, "units")
                elif getattr(event, "num", None) == 4:
                    self.persona_prompt_text.yview_scroll(-1, "units")
                elif getattr(event, "num", None) == 5:
                    self.persona_prompt_text.yview_scroll(1, "units")
            except tk.TclError as exc:
                self._record_ui_warning("soul_text_wheel", exc, 120)
            return "break"
        self.persona_prompt_text.bind("<MouseWheel>", soul_wheel, add="+")
        self.persona_prompt_text.bind("<Button-4>", soul_wheel, add="+")
        self.persona_prompt_text.bind("<Button-5>", soul_wheel, add="+")
        prompt_count = tk.Label(body, text="0/6000", bg=COLORS["bg_card"], fg=COLORS["text_weak"], font=FONTS["small"])
        prompt_count.grid(row=3, column=1, sticky="w", padx=(10, 0))
        def sync_counts(_event: tk.Event | None = None) -> None:
            name = safe_text(self.persona_name_var.get(), 20)
            if name != self.persona_name_var.get():
                self.persona_name_var.set(name)
            self._sync_persona_text_widget()
            prompt = safe_chat_text(self.persona_prompt_var.get(), 6000)
            if prompt != self.persona_prompt_var.get():
                self.persona_prompt_var.set(prompt)
                self.persona_prompt_text.delete("1.0", "end")
                self.persona_prompt_text.insert("1.0", prompt)
            name_count.configure(text=f"{len(name)}/20")
            prompt_count.configure(text=f"{len(prompt)}/6000")
        name_entry.bind("<KeyRelease>", sync_counts, add="+")
        self.persona_prompt_text.bind("<KeyRelease>", sync_counts, add="+")
        self.persona_prompt_text.bind("<FocusOut>", sync_counts, add="+")
        sync_counts()
        make_hint(body, "L6.72.38：Soul 会被投影为 PAD + OCEAN 情感/人格向量，并由 SoulStyleModel 平滑持久化为长期情感底色。除 Soul 与 SoulStyleModelState 外，Runtime / Planner / Tool / Skill / Memory / Provider 只提供事实和边界，不允许改变语气、亲密度、热情度或人味。", bg=COLORS["bg_card"], wraplength=520).grid(row=4, column=1, sticky="ew", padx=(10, 0), pady=(8, 0))
        tk.Button(body, text="保存 Soul", command=self._save_runtime_settings_frontend_only, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=12, pady=5).grid(row=5, column=1, sticky="w", padx=(10, 0), pady=(10, 0))
        return card

    def _build_appearance_settings_card(self, parent: tk.Misc, s: RuntimeSnapshot) -> Card:
        card = Card(parent, "字体与主题", "字体/字号/行距/代码字体/主题即时生效；缩放只改变比例，不改变页面排版结构。")
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14))
        body.grid_columnconfigure(1, weight=1)
        font_labels = {"system": "系统默认", "source_han_sans": "思源黑体", "lxgw_wenkai": "霞鹜文楷", "sarasa_gothic": "更纱黑体"}
        code_labels = {"fira_code": "Fira Code", "cascadia_code": "Cascadia Code", "jetbrains_mono": "JetBrains Mono", "tk_fixed": "系统等宽"}
        row = 0
        tk.Label(body, text="界面字体", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="w", pady=5)
        ui_combo = ttk.Combobox(body, values=list(font_labels.values()), state="readonly")
        ui_combo.set(font_labels.get(self.ui_font_family_var.get(), "系统默认"))
        ui_combo.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        ui_combo.bind("<<ComboboxSelected>>", lambda _e, c=ui_combo: (self.ui_font_family_var.set({v:k for k,v in font_labels.items()}.get(c.get(), "system")), self._apply_typography_selection()), add="+")
        row += 1
        tk.Label(body, text="聊天字号", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="w", pady=5)
        size_box = ttk.Combobox(body, textvariable=self.chat_font_size_var, values=[12, 14, 15, 16, 18], state="readonly")
        size_box.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        size_box.bind("<<ComboboxSelected>>", lambda _e: self._apply_typography_selection(), add="+")
        row += 1
        tk.Label(body, text="显示比例", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="w", pady=5)
        scale_box = ttk.Combobox(body, textvariable=self.settings_scale_var, values=[0.9, 1.0, 1.1, 1.2], state="readonly")
        scale_box.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        scale_box.bind("<<ComboboxSelected>>", lambda _e: self._apply_typography_selection(), add="+")
        row += 1
        tk.Label(body, text="行间距", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="w", pady=5)
        line_box = ttk.Combobox(body, textvariable=self.line_height_var, values=[1.4, 1.6, 1.8, 2.0], state="readonly")
        line_box.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        line_box.bind("<<ComboboxSelected>>", lambda _e: self._apply_typography_selection(), add="+")
        row += 1
        tk.Label(body, text="代码字体", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="w", pady=5)
        code_combo = ttk.Combobox(body, values=list(code_labels.values()), state="readonly")
        code_combo.set(code_labels.get(self.code_font_family_var.get(), "Cascadia Code"))
        code_combo.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        code_combo.bind("<<ComboboxSelected>>", lambda _e, c=code_combo: (self.code_font_family_var.set({v:k for k,v in code_labels.items()}.get(c.get(), "cascadia_code")), self._apply_typography_selection()), add="+")
        row += 1
        tk.Checkbutton(body, text="代码连字", variable=self.code_ligatures_var, command=self._apply_typography_selection, bg=COLORS["bg_card"], fg=COLORS["text_main"], selectcolor=COLORS["bg_input"], activebackground=COLORS["bg_card"], activeforeground=COLORS["text_main"], font=FONTS["small"]).grid(row=row, column=1, sticky="w", padx=(10, 0), pady=5)
        row += 1
        tk.Checkbutton(body, text="紧凑模式", variable=self.compact_mode_var, command=self._on_compact_mode_changed_frontend_only, bg=COLORS["bg_card"], fg=COLORS["text_main"], selectcolor=COLORS["bg_input"], activebackground=COLORS["bg_card"], activeforeground=COLORS["text_main"], font=FONTS["small"]).grid(row=row, column=1, sticky="w", padx=(10, 0), pady=5)
        row += 1
        tk.Label(body, text="主题", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=row, column=0, sticky="nw", pady=(10, 5))
        theme_grid = tk.Frame(body, bg=COLORS["bg_card"])
        theme_grid.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=(8, 5))
        for idx, (key, data) in enumerate(THEME_PROFILES.items()):
            btn = tk.Button(theme_grid, text=data.get("label", key), command=lambda p=key: self._set_theme_profile(p), bg=data.get("accent", COLORS["accent"]), fg="#FFFFFF", relief="flat", padx=10, pady=5, cursor="hand2")
            btn.grid(row=idx // 3, column=idx % 3, sticky="ew", padx=(0, 6), pady=(0, 6))
        row += 1
        tk.Button(body, text="保存外观", command=self._save_ui_preferences, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=12, pady=5).grid(row=row, column=1, sticky="w", padx=(10, 0), pady=(6, 0))
        row += 1
        make_hint(body, "字体选择只声明系统字体名；若本机未安装，Tk 自动 fallback。显示比例只缩放字体，不触发侧栏/卡片重排。", bg=COLORS["bg_card"], wraplength=520).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        return card

    def _build_skill_panel_card(self, parent: tk.Misc, s: RuntimeSnapshot) -> Card:
        card = Card(parent, "技能面板", "技能名称 hover 展示完整描述、最近调用、成功率；开关只提交前端偏好。")
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14))
        body.grid_columnconfigure(0, weight=1)
        search = tk.Entry(body, textvariable=self.skill_search_var, bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat")
        search.grid(row=0, column=0, sticky="ew", pady=(0, 8), ipady=5)
        search.bind("<KeyRelease>", lambda _e: self._schedule_settings_page_refresh(), add="+")
        search.bind("<FocusOut>", lambda _e: self._save_ui_preferences(), add="+")
        query = safe_text(self.skill_search_var.get(), 80).lower()
        for idx, item in enumerate([x for x in self._collect_skill_items(s) if not query or query in x["name"].lower()], start=1):
            self._render_registry_toggle_item(body, idx, item, "skill")
        return card

    def _build_tool_panel_card(self, parent: tk.Misc, s: RuntimeSnapshot) -> Card:
        card = Card(parent, "工具面板", "按 文件 / 网络 / 代码 / 系统 分类展示；hover 展示描述、权限与分类。")
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14))
        body.grid_columnconfigure(0, weight=1)
        search = tk.Entry(body, textvariable=self.tool_search_var, bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat")
        search.grid(row=0, column=0, sticky="ew", pady=(0, 8), ipady=5)
        search.bind("<KeyRelease>", lambda _e: self._schedule_settings_page_refresh(), add="+")
        search.bind("<FocusOut>", lambda _e: self._save_ui_preferences(), add="+")
        tabs = tk.Frame(body, bg=COLORS["bg_card"])
        tabs.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        for label in ("文件", "网络", "代码", "系统"):
            tk.Label(tabs, text=label, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small_bold"], padx=10, pady=4).pack(side="left", padx=(0, 6))
        query = safe_text(self.tool_search_var.get(), 80).lower()
        for idx, item in enumerate([x for x in self._collect_tool_items(s) if not query or query in x["name"].lower() or query in x["category"].lower()], start=2):
            self._render_registry_toggle_item(body, idx, item, "tool")
        return card

    def _build_runtime_status_card(self, parent: tk.Misc, s: RuntimeSnapshot, readiness: Dict[str, Any], identity: Dict[str, Any]) -> Card:
        title = "运行时状态 ▼" if self.runtime_status_expanded else "运行时状态 ▶"
        card = Card(parent, title, "点击展开/收起 CPU | 内存 | API 状态描述。")
        card.bind("<Button-1>", lambda _e: self._toggle_runtime_status_card())
        body = tk.Frame(card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14))
        dots = tk.Frame(body, bg=COLORS["bg_card"])
        dots.grid(row=0, column=0, sticky="w")
        for label, state in (("CPU", "ok"), ("内存", "ok"), ("API", "ok" if readiness.get("readiness") == "ready" else "warning")):
            tk.Label(dots, text=f"● {label}", bg=COLORS["bg_card"], fg=STATUS_COLORS.get(state, COLORS["text_sub"]), font=FONTS["small_bold"]).pack(side="left", padx=(0, 10))
        if self.runtime_status_expanded:
            rows = [("CPU 占用", int(getattr(s, "cpu_percent", 0) or 0)), ("内存 MB", int(getattr(s, "memory_mb", 0) or 0)), ("API 调用", int(getattr(s, "api_call_count", getattr(s, "last_event_seq", 0)) or 0)), ("延迟 ms", int(getattr(s, "latency_ms", 0) or 0))]
            for idx, (label, value) in enumerate(rows, start=1):
                line = tk.Frame(body, bg=COLORS["bg_card"])
                line.grid(row=idx, column=0, sticky="ew", pady=4)
                line.grid_columnconfigure(1, weight=1)
                tk.Label(line, text=f"{label}: {value}", bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["small"]).grid(row=0, column=0, sticky="w")
                bar = ttk.Progressbar(line, style="LZ.Horizontal.TProgressbar", maximum=100, value=max(0, min(100, value if label == "CPU 占用" else value % 100)))
                bar.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        return card

    def _collect_skill_items(self, s: RuntimeSnapshot) -> List[Dict[str, Any]]:
        raw = list(getattr(s, "skill_public_projection", []) or getattr(s, "skills", []) or [])
        items: List[Dict[str, Any]] = []
        for item in raw:
            if isinstance(item, dict):
                name = safe_text(item.get("name") or item.get("skill_name"), 80)
                desc = safe_text(item.get("description") or item.get("summary") or "技能投影", 240)
                success = int(float(item.get("success_rate", 0.8)) * 100) if float(item.get("success_rate", 0.8)) <= 1 else int(item.get("success_rate", 80))
                items.append({"name": name, "description": desc, "recent": safe_text(item.get("last_called") or "未知", 40), "success": success, "category": "Skill", "permission": "Runtime"})
        if not items:
            items = [
                {"name": "学习精通", "description": "目标澄清、分级学习、可信度评估与成果沉淀。", "recent": "本地投影", "success": 86, "category": "Skill", "permission": "Runtime"},
                {"name": "代码逻辑", "description": "跨文件工程感知、测试、回滚、补丁与代码自愈辅助。", "recent": "本地投影", "success": 82, "category": "Skill", "permission": "Runtime"},
                {"name": "WPS 排版", "description": "文档版式、标题层级、导出规范与办公排版经验回路。", "recent": "本地投影", "success": 78, "category": "Skill", "permission": "Runtime"},
            ]
        return items[:24]

    def _collect_tool_items(self, s: RuntimeSnapshot) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for step in list(getattr(s, "execution_steps", []) or []):
            name = safe_text(getattr(step, "name", ""), 80)
            if not name:
                continue
            category = "代码" if "code" in name.lower() or "编译" in name else "系统"
            risk = safe_text(getattr(step, "risk_level", "A2"), 20)
            items.append({"name": name, "description": safe_text(getattr(step, "output_summary", "运行时工具投影"), 240), "recent": safe_text(getattr(step, "status", "未知"), 40), "success": 80, "category": category, "permission": risk})
        if not items:
            items = [
                {"name": "文件读写", "description": "经 Runtime / 工作区授权链路读取和写入文件。", "recent": "待机", "success": 85, "category": "文件", "permission": "A2/A3"},
                {"name": "网络检索", "description": "经 NetworkPolicy 与 QualityGate 管控的网络访问。", "recent": "待机", "success": 72, "category": "网络", "permission": "A2/A3"},
                {"name": "代码执行", "description": "在沙箱或本地运行时授权范围内执行编译/测试命令。", "recent": "待机", "success": 81, "category": "代码", "permission": "A3"},
                {"name": "系统自检", "description": "启动、自检、依赖检查、桥接与审计回放。", "recent": "待机", "success": 88, "category": "系统", "permission": "A1/A2"},
            ]
        return items[:40]

    def _render_registry_toggle_item(self, parent: tk.Misc, row: int, item: Dict[str, Any], kind: str) -> None:
        name = safe_text(item.get("name"), 80)
        key = f"{kind}:{name}"
        if not hasattr(self, "_registry_toggle_vars"):
            self._registry_toggle_vars = {}
        if key not in self._registry_toggle_vars:
            disabled = set(self._ui_prefs_cache.get(f"disabled_{kind}s", []) or [])
            self._registry_toggle_vars[key] = tk.BooleanVar(value=name not in disabled)
        box = tk.Frame(parent, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
        box.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        box.grid_columnconfigure(0, weight=1)
        success = int(item.get("success", 0) or 0)
        badge_color = COLORS["success"] if success > 80 else COLORS["warning"] if success >= 50 else COLORS["danger"]
        title = tk.Label(box, text=name, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["body_bold"], anchor="w", justify="left", wraplength=360)
        title.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
        desc_short = safe_text(item.get("description", ""), 30)
        tk.Label(box, text=desc_short, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], anchor="w", justify="left", wraplength=360).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        tk.Label(box, text=f"{success}%", bg=badge_color, fg="#FFFFFF", font=FONTS["small_bold"], padx=8, pady=3).grid(row=0, column=1, sticky="e", padx=8, pady=(8, 2))
        tk.Checkbutton(box, variable=self._registry_toggle_vars[key], command=lambda n=name, k=kind: self._save_registry_toggle(k, n), bg=COLORS["bg_card_2"], activebackground=COLORS["bg_card_2"], selectcolor=COLORS["bg_input"]).grid(row=1, column=1, sticky="e", padx=8, pady=(0, 8))
        Tooltip(title, f"{name}\n描述：{safe_text(item.get('description', ''), 300)}\n最近调用：{safe_text(item.get('recent', '未知'), 80)}\n成功率：{success}%\n分类：{safe_text(item.get('category', ''), 80)}\n所需权限：{safe_text(item.get('permission', ''), 80)}")

    def _provider_readiness_public(self, provider_settings: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return provider_readiness_from_public_projection(provider_settings).to_dict()
        except Exception as exc:
            return {
                "readiness": "unknown",
                "label": "模型服务状态未知",
                "missing_fields": [],
                "effective_backend_mode": "unknown",
                "requested_backend_mode": "unknown",
                "primary_action": "刷新快照",
                "can_use_real_model": False,
                "mock_mode": False,
                "message": safe_text(exc, 180),
            }

    def _provider_public_from_snapshot(self, s: RuntimeSnapshot) -> Dict[str, Any]:
        return {
            "provider": safe_text(getattr(s, "model_provider", ""), 80),
            "model": safe_text(getattr(s, "provider_model", ""), 80),
            "provider_config_state": safe_text(getattr(s, "provider_config_state", "idle"), 80),
            "message": safe_text(getattr(s, "provider_config_message", ""), 220),
            "config_error_code": safe_text(getattr(s, "provider_config_error_code", ""), 80),
            "audit_id": safe_text(getattr(s, "provider_config_audit_id", ""), 80),
            "api_key_configured": bool(getattr(s, "provider_api_key_configured", False)),
            "api_key_digest": safe_text(getattr(s, "provider_api_key_digest", ""), 32),
            "base_url_configured": bool(getattr(s, "provider_base_url_configured", False)),
            "base_url_digest": safe_text(getattr(s, "provider_base_url_digest", ""), 32),
            "base_url_display": safe_text(getattr(self, "api_base_url_var", tk.StringVar(value="")).get(), 220),
            "last_provider_check_state": safe_text(getattr(s, "last_provider_check_state", ""), 60),
            "last_provider_error_code": safe_text(getattr(s, "last_provider_error_code", ""), 80),
            "last_provider_error_message": safe_text(getattr(s, "last_provider_error_message", ""), 180),
            "last_provider_next_action": safe_text(getattr(s, "last_provider_next_action", ""), 120),
            "effective_backend_mode": "provider" if bool(getattr(s, "provider_api_key_configured", False)) and bool(getattr(s, "provider_base_url_configured", False)) else "not_configured",
            "requested_backend_mode": "auto",
            "tool_execution_mode": safe_text(getattr(s, "tool_execution_mode", "runtime_governed"), 80),
            "host_access_scope": host_access_scope_value(getattr(self, "host_access_scope_var", tk.StringVar(value="system_drive")).get()),
            "host_access_root": safe_path_setting_value(getattr(self, "host_access_root_var", tk.StringVar(value="")).get(), 520),
            "persona_name": safe_text(getattr(self, "persona_name_var", tk.StringVar(value="临渊者")).get(), 32),
        }

    def _provider_status_color(self, readiness: Dict[str, Any]) -> str:
        state = safe_text(readiness.get("readiness", ""), 40)
        if state in {"ready", "就绪"}:
            return COLORS["success"]
        if state in {"error", "forced_mock"}:
            return COLORS["danger"]
        if state in {"missing_credentials", "saved_waiting_runtime"}:
            return COLORS["warning"]
        return COLORS["text_sub"]

    def _hydrate_provider_form_from_public(self, provider_settings: Dict[str, Any]) -> None:
        """Load safe provider/model projection into the form without exposing secrets."""
        provider = safe_text(provider_settings.get("provider", ""), 40)
        model = safe_text(provider_settings.get("model", provider_settings.get("main_model", "")), 100)
        base_display = safe_text(
            provider_settings.get("base_url_display")
            or provider_settings.get("provider_base_display")
            or "",
            220,
        )
        tool_mode = safe_text(provider_settings.get("tool_execution_mode", ""), 40)
        host_scope = safe_text(provider_settings.get("host_access_scope", ""), 40)
        host_root = safe_path_setting_value(provider_settings.get("host_access_root", ""), 520)
        persona_name = safe_text(provider_settings.get("persona_name", ""), 32)
        if provider:
            self.api_provider_var.set(provider.split("/", 1)[0].strip() or provider)
        if model:
            self.main_model_var.set(model)
        if base_display and not self.api_base_url_var.get().strip():
            self.api_base_url_var.set(base_display)
        if tool_mode:
            self.tool_execution_mode_var.set(permission_mode_label(tool_mode if tool_mode in {"runtime_governed", "disabled"} else "runtime_governed"))
        if host_scope:
            self.host_access_scope_var.set(host_access_scope_label(host_scope))
        if host_root and not self.host_access_root_var.get().strip():
            self.host_access_root_var.set(host_root)
        if persona_name:
            self.persona_name_var.set(persona_name)
        readiness = self._provider_readiness_public(provider_settings)
        if provider_settings or readiness.get("readiness") != "unknown":
            self.settings_status_var.set(
                "模型服务状态："
                f"{safe_text(readiness.get('label', '未知'), 40)}；"
                f"模式={ui_text(safe_text(readiness.get('effective_backend_mode', 'unknown'), 40))}；"
                f"权限={permission_mode_label(permission_mode_value(self.tool_execution_mode_var.get()))}；"
                f"下一步={safe_text(readiness.get('primary_action', '刷新快照'), 80)}。"
                "接口密钥不回填；服务地址可显示和复用。"
            )

    def _populate_provider_readiness_banner(self, parent: tk.Misc, provider_settings: Dict[str, Any], row: int) -> int:
        readiness = self._provider_readiness_public(provider_settings)
        box = tk.Frame(parent, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
        box.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        box.grid_columnconfigure(0, weight=1)
        tk.Label(
            box,
            text=ui_text(safe_text(readiness.get("label", "模型服务状态未知"), 80)),
            bg=COLORS["bg_card_2"],
            fg=self._provider_status_color(readiness),
            font=FONTS["body_bold"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=(9, 2))
        tk.Label(
            box,
            text=ui_text(safe_text(readiness.get("message", "请检查模型服务配置。"), 220)),
            bg=COLORS["bg_card_2"],
            fg=COLORS["text_sub"],
            font=FONTS["small"],
            wraplength=430,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        meta = (
            f"模式={ui_text(safe_text(readiness.get('effective_backend_mode', 'unknown'), 40))} · "
            f"缺少={'、'.join(readiness.get('missing_fields', []) or []) or '无'} · "
            f"错误={safe_text(readiness.get('config_error_code', '') or '无', 80)} · "
            f"下一步={safe_text(readiness.get('primary_action', '刷新快照'), 80)}"
        )
        tk.Label(box, text=meta, bg=COLORS["bg_card_2"], fg=COLORS["text_weak"], font=FONTS["small"], anchor="w", justify="left", wraplength=520).grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 9))
        return row + 1

    # L6.72.30: removed inactive legacy _populate_api_model_settings().
    # The single active model-management UI is _build_model_management_card().

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
                    allowed = {"provider", "model", "base_url_digest", "base_url_configured", "api_key_digest", "api_key_configured", "timeout", "stream", "planner_mode", "tool_execution_mode", "status", "provider_config_state", "config_error_code", "message", "audit_id", "requires_restart", "frontend_contract", "requested_backend_mode", "effective_backend_mode", "runtime_credential_persisted", "runtime_credential_store_digest", "provider_readiness", "readiness_label", "missing_fields", "next_action", "config_location_hint", "config_file_state", "config_file_exists", "config_path_digest", "local_bridge_can_persist", "raw_secret_visible_to_frontend", "last_provider_check_state", "last_provider_error_code", "last_provider_error_message", "last_provider_next_action", "last_provider_elapsed", "last_provider_audit_id", "provider_hint", "model_candidates", "base_url_display", "persona_name", "persona_digest", "persona_prompt_digest", "host_access_scope", "host_access_root", "host_access_label", "host_access_root_digest", "host_access_root_name", "host_access_runtime_only"}
                    safe: Dict[str, Any] = {}
                    for k, v in data.items():
                        if k not in allowed:
                            continue
                        safe_key = safe_text(k, 80)
                        if safe_key == "missing_fields" and isinstance(v, list):
                            safe[safe_key] = [safe_text(item, 40) for item in v if safe_text(item, 40)]
                        elif isinstance(v, bool):
                            safe[safe_key] = v
                        elif isinstance(v, (int, float)):
                            safe[safe_key] = v
                        else:
                            safe[safe_key] = safe_path_setting_value(v, 520) if safe_key == "host_access_root" else safe_text(v, 180)
                    return safe
            except Exception as exc:
                return {"read_error": safe_text(exc, 160)}
        return {}

    def _project_root(self) -> Path:
        try:
            return Path(__file__).resolve().parents[3]
        except Exception:
            return Path.cwd()

    def _dataup_core_script(self) -> Path:
        return self._project_root() / "scripts" / "dataup_update_core_l6717.py"

    def _run_dataup_command(self, args: List[str], *, label: str, timeout: int = 240) -> None:
        """Launch the standalone DataUp helper from UI chrome.

        The Tk frontend does not copy files. It only starts the updater helper
        after user intent is explicit; the helper owns 清单 validation,
        rollback creation, allow/deny path checks, self-checks and rollback.
        """
        script = self._dataup_core_script()
        if not script.exists():
            self.dataup_status_var.set("数据更新器缺失：scripts/dataup_update_core_l6717.py")
            return
        root = self._project_root()
        cmd = [sys.executable, str(script), "--root", str(root), *args]
        self.dataup_status_var.set(f"数据更新：{label} 已启动，等待更新器回执……")

        def worker() -> None:
            try:
                env = dict(**__import__("os").environ)
                env["PYTHONIOENCODING"] = "utf-8"
                proc = subprocess.run(cmd, cwd=str(root), env=env, text=True, capture_output=True, timeout=timeout)
                output = "\n".join(x for x in (proc.stdout, proc.stderr) if x).strip()
                summary = self._summarize_dataup_output(output, proc.returncode)
            except subprocess.TimeoutExpired:
                summary = f"数据更新：{label} 超时；未确认更新成功，请查看 reports/dataup_last_update_report_l6717.json。"
            except Exception as exc:
                summary = f"数据更新：{label} 启动失败：{safe_text(exc, 180)}"
            self._post_to_ui(lambda text=summary: self.dataup_status_var.set(text))

        threading.Thread(target=worker, daemon=True).start()

    def _summarize_dataup_output(self, output: str, returncode: int) -> str:
        try:
            start = output.find("{")
            data = json.loads(output[start:] if start >= 0 else output)
            ok = bool(data.get("ok"))
            stage = safe_text(data.get("stage", "unknown"), 80)
            report = safe_text(data.get("report", "reports/dataup_last_update_report_l6717.json"), 120)
            if data.get("latest_check") and stage == "latest_check":
                latest = data.get("latest_check", {})
                source = safe_text(latest.get("source_name", "auto"), 40) if isinstance(latest, dict) else "auto"
                return f"数据更新：检查更新{'成功' if ok else '失败'}；来源={source}；报告={report}"
            plan = data.get("plan", {}) if isinstance(data.get("plan"), dict) else {}
            version = safe_text(plan.get("version", "未知版本"), 80)
            files = plan.get("file_count", 0)
            blocked = plan.get("blocked", [])
            if ok and stage == "applied":
                return f"数据更新：更新完成；版本={version}；文件数={files}；已创建回滚点；请重启桌面端。报告={report}"
            if ok:
                return f"数据更新：校验通过；阶段={stage}；版本={version}；文件数={files}；报告={report}"
            if blocked:
                return f"数据更新：已阻断；阶段={stage}；已阻断={safe_text('；'.join(str(x) for x in blocked[:3]), 220)}；报告={report}"
            return f"数据更新：执行失败；阶段={stage}；返回码={returncode}；错误={safe_text(data.get('error', ''), 180)}；报告={report}"
        except Exception:
            tail = safe_text(output[-500:], 500) if output else "无输出"
            return f"数据更新：返回码={returncode}；输出摘要：{tail}"

    def _dataup_check_update(self) -> None:
        self._run_dataup_command(["--check", "--source", "auto"], label="检查更新", timeout=60)

    def _dataup_auto_update(self) -> None:
        approved = messagebox.askyesno(
            "DataUp 一键安全更新",
            "将从 Gitee 主源 / GitHub 备源读取 数据更新索引文件，下载 数据更新包，并执行：清单校验、路径白名单、回滚点、自检、失败回滚。\n\n"
            "不会覆盖 模型服务配置、接口密钥、记忆、日志、审计私密数据或工作区。是否继续？",
        )
        if not approved:
            self.dataup_status_var.set("数据更新：用户取消一键安全更新。")
            return
        self._run_dataup_command(["--source", "auto", "--apply", "--yes"], label="一键安全更新", timeout=360)

    def _dataup_select_package(self) -> None:
        path = filedialog.askopenfilename(
            title="选择数据更新包",
            filetypes=[("数据更新 zip", "*.zip"), ("All files", "*.*")],
        )
        if not path:
            self.dataup_status_var.set("数据更新：未选择本地更新包。")
            return
        approved = messagebox.askyesno(
            "应用本地 数据更新包",
            "将对所选 zip 执行 数据更新安全流程：清单校验、路径白名单、回滚点、自检、失败回滚。\n\n是否继续？",
        )
        if not approved:
            self.dataup_status_var.set("数据更新：用户取消本地包更新。")
            return
        self._run_dataup_command(["--package", path, "--apply", "--yes"], label="本地包安全更新", timeout=360)

    def _show_dataup_boundary(self) -> None:
        self._show_safe_detail("数据更新边界", [
            "一键更新按钮只启动 scripts/dataup_update_core_l6717.py，不由 Tk 前端直接复制或覆盖文件。",
            "允许覆盖：frontend/、desktop/、scripts/、docs/、reports/、launchers/、installer/updater/、01_启动入口/、dataup/ 与根目录说明文件。",
            "默认阻断：模型服务配置、接口密钥、.env、记忆、日志、审计私密数据、credentials、工作区私密数据、backend/runtime 核心路径。",
            "更新前创建 backups/dataup_rollback_YYYYMMDD_HHMMSS 回滚点。",
            "更新后执行 compileall、secret scan、desktop bundle preflight；失败则自动回滚。",
            "Gitee 主源：https://gitee.com/yu-yongxiang1994/natures-craftsmanship",
            "GitHub 备源：https://github.com/simahanfeng007-lgtm/Tian.Gong.Zao.Wu",
            "签名验签槽已预留；当前 标准库 更新器执行 清单 SHA-256 校验，不把未实现的签名验真说成已完成。",
        ])

    def _page_header(self, root: tk.Misc, title: str, subtitle: str) -> tk.Frame:
        frame = tk.Frame(root, bg=COLORS["bg_root"])
        frame.grid_columnconfigure(0, weight=1)
        make_section_title(frame, title).grid(row=0, column=0, sticky="w")
        # L6.72.24: page subtitles are suppressed. The sidebar already names
        # the page, and dense explanatory copy below every title was causing
        # overflow/noise in the desktop shell.
        return frame

    def _build_files_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        wrap = tk.Frame(root, bg=COLORS["bg_root"])
        wrap.grid(row=0, column=0, sticky="nsew", padx=DIMENS["page_pad"], pady=DIMENS["page_pad"])
        wrap.grid_columnconfigure(0, weight=1)
        header = self._page_header(wrap, "文件传输", "上传/下载都必须走 运行时 / 天工网关 授权链路；前端只提交脱敏请求与展示回执。")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        action_card = Card(wrap, "文件入口")
        action_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        body = tk.Frame(action_card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        make_hint(
            body,
            "选择本地文件后，前端只计算文件名、大小、摘要和用途，向 运行时 提交 transfer request；不把原始路径、文件正文、密钥或端点写入报告。",
            bg=COLORS["bg_card"],
            wraplength=760,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        btn_row = tk.Frame(body, bg=COLORS["bg_card"])
        btn_row.grid(row=1, column=0, sticky="w")
        tk.Button(btn_row, text="选择文件并提交", command=self._request_file_transfer_from_dialog, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=16, pady=7).pack(side="left", padx=(0, 8))
        tk.Checkbutton(btn_row, text="上传后自动进入 运行时文件处理", variable=self.file_auto_run_var, bg=COLORS["bg_card"], fg=COLORS["text_sub"], selectcolor=COLORS["bg_input"], activebackground=COLORS["bg_card"], activeforeground=COLORS["text_main"], relief="flat").pack(side="left", padx=(0, 8))
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
            title = f"{safe_text(getattr(rec, 'file_name', 'attachment'), 80)} · {getattr(rec, 'size_bytes', 0)} 字节 · {safe_text(getattr(rec, 'status', ''), 40)}"
            tk.Label(row, text=title, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
            msg = f"摘要指纹={safe_text(getattr(rec, 'sha256_digest', ''), 24) or '无'} · 审计={safe_text(getattr(rec, 'audit_id', ''), 32) or '无'} · {safe_text(getattr(rec, 'message', ''), 160)}"
            tk.Label(row, text=msg, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=760, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
        tk.Button(records_card, text="文件传输边界详情", command=self._show_file_transfer_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 14))

    def _build_connectors_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        wrap = tk.Frame(root, bg=COLORS["bg_root"])
        wrap.grid(row=0, column=0, sticky="nsew", padx=DIMENS["page_pad"], pady=DIMENS["page_pad"])
        wrap.grid_columnconfigure(0, weight=1)
        header = self._page_header(wrap, "连接器注册表", "白名单、签名摘要、隔离状态和注册请求只读展示；前端不安装、不执行、不存密钥、不直连连接器市场。")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        policy_card = Card(wrap, "注册表策略")
        policy_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        projection = getattr(s, "connector_registry_projection", None)
        body = tk.Frame(policy_card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        values = [
            ("状态", safe_text(getattr(s, "connector_registry_state", "就绪"), 80)),
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
        make_hint(req_body, "提交时只生成 连接器注册信封：显示名称、类型、清单摘要、来源摘要、作用域。不会保存原始端点、密钥、清单正文，也不会安装连接器服务。", bg=COLORS["bg_card"], wraplength=760).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        tk.Label(req_body, text="名称", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=1, column=0, sticky="w", pady=4)
        self.connector_name_var = tk.StringVar(value="本地候选连接器")
        tk.Entry(req_body, textvariable=self.connector_name_var, bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat").grid(row=1, column=1, sticky="ew", pady=4)
        tk.Label(req_body, text="类型", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=2, column=0, sticky="w", pady=4)
        self.connector_kind_var = tk.StringVar(value="MCP 服务")
        ttk.Combobox(req_body, textvariable=self.connector_kind_var, values=("MCP 服务", "本地连接器", "远程连接器", "文档连接器", "浏览器连接器", "工作流连接器"), state="readonly").grid(row=2, column=1, sticky="ew", pady=4)
        btn_row = tk.Frame(req_body, bg=COLORS["bg_card"])
        btn_row.grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))
        tk.Button(btn_row, text="提交注册请求", command=self._request_connector_registration, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=16, pady=7).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="刷新", command=lambda: self.show_page("connectors"), bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=14, pady=7).pack(side="left")
        tk.Label(req_body, textvariable=self.connector_status_var, bg=COLORS["bg_card"], fg=COLORS["text_weak"], font=FONTS["small"], wraplength=760, justify="left").grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))

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
            msg = f"清单摘要指纹={safe_text(getattr(rec, 'manifest_digest', ''), 24) or '无'} · 可信度={safe_text(getattr(rec, 'trust_level', ''), 40)} · 审计={safe_text(getattr(rec, 'audit_id', ''), 32) or '无'} · {safe_text(getattr(rec, 'message', ''), 160)}"
            tk.Label(row, text=msg, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=760, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
        for item in manifests:
            row = tk.Frame(inner, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            row.grid(row=row_idx, column=0, sticky="ew", pady=(0, 8)); row.grid_columnconfigure(0, weight=1); row_idx += 1
            title = f"清单 · {safe_text(getattr(item, 'display_name', ''), 80)} · {safe_text(getattr(item, 'default_mode', ''), 40)} · 隔离={getattr(item, 'quarantined', False)}"
            tk.Label(row, text=title, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
            msg = f"类型={safe_text(getattr(item, 'kind', ''), 40)} · 摘要指纹={safe_text(getattr(item, 'manifest_digest', ''), 24)} · 作用域={safe_text(','.join(getattr(item, 'requested_scopes', []) or []), 120)}"
            tk.Label(row, text=msg, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=760, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
        tk.Button(records_card, text="连接器边界详情", command=self._show_connector_detail, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=5).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 14))

    def _build_workspace_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        wrap = tk.Frame(root, bg=COLORS["bg_root"])
        wrap.grid(row=0, column=0, sticky="nsew", padx=DIMENS["page_pad"], pady=DIMENS["page_pad"])
        wrap.grid_columnconfigure(0, weight=1)
        header = self._page_header(wrap, "工作区 / 沙箱边界", "工作区、目录白名单、文件授权和下载中转只读展示；前端只提交授权请求，不创建工作区、不改访问控制、不复制文件。")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        policy_card = Card(wrap, "工作区策略")
        policy_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        policy = getattr(s, "workspace_policy", None)
        body = tk.Frame(policy_card, bg=COLORS["bg_card"])
        body.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 14))
        body.grid_columnconfigure(0, weight=1)
        values = [
            ("状态", safe_text(getattr(s, "workspace_state", "就绪"), 80)),
            ("根目录摘要指纹", safe_text(getattr(policy, "root_digest", "") or "未公开", 32)),
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
        make_hint(auth_body, "只读授权会选择输入文件；写入授权只选择输出目录/目标位置，不上传文件正文。两者都只生成授权 信封：文件名、模式、作用域、路径摘要。", bg=COLORS["bg_card"], wraplength=760).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        btn_row = tk.Frame(auth_body, bg=COLORS["bg_card"])
        btn_row.grid(row=1, column=0, sticky="w")
        tk.Button(btn_row, text="申请只读授权", command=lambda: self._request_file_authorization_from_dialog("read"), bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=16, pady=7).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="选择输出目录并申请写入", command=lambda: self._request_file_authorization_from_dialog("write"), bg=COLORS["warning"], fg="#FFFFFF", relief="flat", padx=16, pady=7).pack(side="left", padx=(0, 8))
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
            msg = f"作用域={safe_text(getattr(rec, 'scope', ''), 60)} · 路径摘要指纹={safe_text(getattr(rec, 'path_digest', ''), 24) or '无'} · 审计={safe_text(getattr(rec, 'audit_id', ''), 32) or '无'} · {safe_text(getattr(rec, 'message', ''), 160)}"
            tk.Label(row, text=msg, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=760, justify="left").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
        for rec in dl_records:
            row = tk.Frame(inner, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
            row.grid(row=row_idx, column=0, sticky="ew", pady=(0, 8)); row.grid_columnconfigure(0, weight=1); row_idx += 1
            title = f"下载中转 · {safe_text(getattr(rec, 'file_name', ''), 80)} · {safe_text(getattr(rec, 'status', ''), 40)}"
            tk.Label(row, text=title, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], font=FONTS["body_bold"]).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
            msg = f"产物摘要指纹={safe_text(getattr(rec, 'artifact_id_digest', ''), 24)} · 令牌摘要指纹={safe_text(getattr(rec, 'download_token_digest', ''), 24)} · {safe_text(getattr(rec, 'message', ''), 160)}"
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
            "runtime_status": f"{self._status_short(s.current_task_status)} · {safe_text(s.runtime_status, 24)}",
            "backend_mode": self._home_mode_label(s),
            "gate_status": f"质量门 {safe_text(getattr(s, 'gate_status', s.quality_gate_status), 24)}",
            "audit_id": f"审计 {safe_text(getattr(s, 'audit_id', s.evidence_ref), 24)}",
        }
        for key, label in self.status_labels.items():
            label.configure(text=values.get(key, key), fg=COLORS["text_sub"], bg=COLORS["bg_window"])
        self._refresh_theme_switch_buttons()

    def _status_cn(self, status: str) -> str:
        return {
            "succeeded": "完成",
            "running": "进行中",
            "queued": "排队",
            "已阻断": "阻塞",
            "failed": "失败",
            "confirmation_required": "待确认",
            "recovered": "已恢复",
            "timeout": "超时",
        }.get(status, status)
