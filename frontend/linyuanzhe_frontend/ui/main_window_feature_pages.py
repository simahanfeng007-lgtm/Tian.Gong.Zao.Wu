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


class FeaturePagesMixin:
    def _build_sessions_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(root, "任务", "多任务只读投影、搜索、恢复请求、等待确认、失败归档；不直接恢复工具或应用回滚。").grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

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
        """Compact memory cockpit.

        STEP31E removes the large empty memory surface. The page now shows one
        dense summary band, five memory levels, recall/forget indicators and
        recent sanitized chat snippets. It remains PublicProjection-only.
        """
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(root, "记忆", "五层记忆、召回、遗忘与经验升级的紧凑投影。只显示 sanitized summary / digest / evidence_ref。") .grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(2, weight=1)

        summary = Card(body, "记忆摘要 / Recall Snapshot")
        summary.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        summary.grid_columnconfigure(0, weight=1)
        make_hint(summary, s.memory_sanitized_summary or "暂无 Runtime 记忆摘要；等待 PublicProjection 回填。", bg=COLORS["bg_card"], wraplength=1120).grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 8))
        meta = tk.Frame(summary, bg=COLORS["bg_card"])
        meta.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))
        for col in range(4):
            meta.grid_columnconfigure(col, weight=1)
        LabeledValue(meta, "digest", s.memory_digest or "无").grid(row=0, column=0, sticky="ew", padx=(0, 8))
        LabeledValue(meta, "evidence_ref", s.memory_evidence_ref or "无").grid(row=0, column=1, sticky="ew", padx=(0, 8))
        LabeledValue(meta, "mode", getattr(s, "memory_mode", "frontend_no_direct_write")).grid(row=0, column=2, sticky="ew", padx=(0, 8))
        LabeledValue(meta, "visible_msgs", str(getattr(s, "visible_message_count", len(getattr(s, "chat_messages", []) or [])))).grid(row=0, column=3, sticky="ew")

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
            ("召回状态", "等待 Runtime recall projection" if not s.memory_digest else "摘要可用"),
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
        make_hint(recent, "边界：此页只读展示 PublicProjection，不展示原始记忆正文、不展示隐私原文、不写记忆、不写审计、不触发回滚。", bg=COLORS["bg_card"], wraplength=1120).grid(row=max(2, len(messages) + 1), column=0, sticky="ew", padx=14, pady=(10, 14))

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

    def _build_four_paths_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        self._page_header(root, "系统", "执行、记忆、情志、生命周期与 DataUp 社区更新入口；首页不展示更新按钮，避免误触。") .grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
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

        dataup = Card(body, "DataUp 社区安全更新")
        dataup.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        dataup_body = tk.Frame(dataup, bg=COLORS["bg_card"])
        dataup_body.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14))
        dataup_body.grid_columnconfigure(0, weight=1)
        make_hint(
            dataup_body,
            "更新源：Gitee 主源 + GitHub 备源。点击一键安全更新时，前端只启动独立 DataUp 更新器；更新器负责 manifest 校验、路径白名单、回滚点、自检和失败回滚。不会覆盖 Provider 配置、密钥、记忆、日志、审计私密数据或工作区。",
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
        tk.Button(btns, text="选择本地 DataUp 包", command=self._dataup_select_package, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=12, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="更新边界", command=self._show_dataup_boundary, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=12, pady=5).pack(side="left")
        tk.Label(dataup_body, textvariable=self.dataup_status_var, bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"], wraplength=980, justify="left", anchor="w").grid(row=3, column=0, sticky="ew")

        digest = Card(body, "统一 PlannerContext")
        digest.grid(row=3, column=0, columnspan=2, sticky="ew")
        LabeledValue(digest, "context_digest", status.planner_context_digest).grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 4))
        make_hint(digest, status.hard_boundary_summary, bg=COLORS["bg_card"]).grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 14))

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

    def _build_settings_page(self, root: tk.Frame, s: RuntimeSnapshot) -> None:
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self._page_header(root, "设置", "Provider 配置向导、主模型、外观与 Runtime 只读接入集中在设置页；首页不展示密钥或复杂配置。") .grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        body = tk.Frame(root, bg=COLORS["bg_root"])
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        identity = self._get_product_identity_public()
        provider_settings = self._get_provider_settings_public()
        readiness = self._provider_readiness_public(provider_settings)
        self._hydrate_provider_form_from_public(provider_settings)

        model_card = Card(body, "Provider 配置向导")
        model_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._populate_api_model_settings(model_card, provider_settings)

        status = Card(body, "RuntimeClient 状态")
        status.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
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
            ("readiness", readiness.get("label", "未读取")),
            ("missing_fields", "、".join(readiness.get("missing_fields", [])) or "无"),
            ("backend_mode", provider_settings.get("effective_backend_mode") or provider_settings.get("requested_backend_mode") or "未读取"),
            ("provider_config_state", provider_settings.get("status") or provider_settings.get("provider_config_state") or getattr(s, "provider_config_state", "未提交")),
            ("config_error_code", provider_settings.get("config_error_code") or getattr(s, "provider_config_error_code", "无") or "无"),
            ("last_provider_check", provider_settings.get("last_provider_check_state") or "not_tested"),
            ("last_provider_error", provider_settings.get("last_provider_error_code") or "无"),
            ("last_provider_next", provider_settings.get("last_provider_next_action") or readiness.get("primary_action") or "无"),
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

        appearance = tk.Frame(operations, bg=COLORS["bg_card"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
        appearance.grid(row=3, column=0, sticky="ew", padx=14, pady=(4, 14))
        appearance.grid_columnconfigure(1, weight=1)
        tk.Label(appearance, text="桌面配色", bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small_bold"]).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))
        values = [f"{key} · {data.get('label', key)}" for key, data in THEME_PROFILES.items()]
        combo = ttk.Combobox(appearance, values=values, state="readonly")
        current = self.theme_profile_var.get()
        combo.set(f"{current} · {THEME_PROFILES.get(current, {}).get('label', current)}")
        combo.grid(row=0, column=1, sticky="ew", padx=(8, 10), pady=(10, 6))
        def select_theme(_event=None, box=combo):
            raw = safe_text(box.get(), 80)
            self.theme_profile_var.set(raw.split("·", 1)[0].strip() or "midnight")
            self._apply_theme_selection()
        combo.bind("<<ComboboxSelected>>", select_theme)
        make_hint(appearance, "可选：永夜 / 极昼 / 墨绿。底框提供永夜/极昼快速切换；只影响前端显示，不影响 Runtime、工具、记忆或审计。", bg=COLORS["bg_card"], wraplength=460).grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

    def _provider_readiness_public(self, provider_settings: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return provider_readiness_from_public_projection(provider_settings).to_dict()
        except Exception as exc:
            return {
                "readiness": "unknown",
                "label": "Provider 状态未知",
                "missing_fields": [],
                "effective_backend_mode": "unknown",
                "requested_backend_mode": "unknown",
                "primary_action": "刷新快照",
                "can_use_real_model": False,
                "mock_mode": True,
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
            "last_provider_check_state": safe_text(getattr(s, "last_provider_check_state", ""), 60),
            "last_provider_error_code": safe_text(getattr(s, "last_provider_error_code", ""), 80),
            "last_provider_error_message": safe_text(getattr(s, "last_provider_error_message", ""), 180),
            "last_provider_next_action": safe_text(getattr(s, "last_provider_next_action", ""), 120),
            "effective_backend_mode": "provider" if bool(getattr(s, "provider_api_key_configured", False)) and bool(getattr(s, "provider_base_url_configured", False)) else "mock",
            "requested_backend_mode": "auto",
        }

    def _provider_status_color(self, readiness: Dict[str, Any]) -> str:
        state = safe_text(readiness.get("readiness", ""), 40)
        if state == "ready":
            return COLORS["success"]
        if state in {"error", "forced_mock"}:
            return COLORS["danger"]
        if state in {"missing_credentials", "saved_waiting_runtime"}:
            return COLORS["warning"]
        return COLORS["text_sub"]

    def _provider_path_hint_text(self) -> str:
        return (
            "配置文件由 Runtime / 本地桥接托管。默认位置："
            "Windows=%APPDATA%\\LinyuanzheDesktop\\provider_config.json；"
            "macOS=~/Library/Application Support/LinyuanzheDesktop/provider_config.json；"
            "Linux=$XDG_CONFIG_HOME/linyuanzhe_desktop/provider_config.json。"
            "UI 不展示、不导出 API Key 或 Base URL 明文。"
        )

    def _hydrate_provider_form_from_public(self, provider_settings: Dict[str, Any]) -> None:
        """Load safe provider/model projection into the form without exposing secrets."""
        provider = safe_text(provider_settings.get("provider", ""), 40)
        model = safe_text(provider_settings.get("model", provider_settings.get("main_model", "")), 100)
        if provider:
            # Local bridge may return a display label like "provider / model".
            self.api_provider_var.set(provider.split("/", 1)[0].strip() or provider)
        if model:
            self.main_model_var.set(model)
        readiness = self._provider_readiness_public(provider_settings)
        if provider_settings or readiness.get("readiness") != "unknown":
            self.settings_status_var.set(
                "Provider 状态："
                f"{safe_text(readiness.get('label', '未知'), 40)}；"
                f"mode={safe_text(readiness.get('effective_backend_mode', 'unknown'), 40)}；"
                f"action={safe_text(readiness.get('primary_action', '刷新快照'), 80)}。"
                "Key/Base URL 明文不回填到前端输入框。"
            )

    def _populate_provider_readiness_banner(self, parent: tk.Misc, provider_settings: Dict[str, Any], row: int) -> int:
        readiness = self._provider_readiness_public(provider_settings)
        box = tk.Frame(parent, bg=COLORS["bg_card_2"], highlightbackground=COLORS["border_soft"], highlightthickness=1)
        box.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        box.grid_columnconfigure(0, weight=1)
        tk.Label(
            box,
            text=safe_text(readiness.get("label", "Provider 状态未知"), 80),
            bg=COLORS["bg_card_2"],
            fg=self._provider_status_color(readiness),
            font=FONTS["body_bold"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=(9, 2))
        tk.Label(
            box,
            text=safe_text(readiness.get("message", "请检查 Provider 配置。"), 220),
            bg=COLORS["bg_card_2"],
            fg=COLORS["text_sub"],
            font=FONTS["small"],
            wraplength=430,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        meta = (
            f"mode={safe_text(readiness.get('effective_backend_mode', 'unknown'), 40)} · "
            f"missing={','.join(readiness.get('missing_fields', []) or []) or 'none'} · "
            f"error={safe_text(readiness.get('config_error_code', '') or 'none', 80)} · "
            f"next={safe_text(readiness.get('primary_action', '刷新快照'), 80)}"
        )
        tk.Label(box, text=meta, bg=COLORS["bg_card_2"], fg=COLORS["text_weak"], font=FONTS["small"], anchor="w").grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 9))
        return row + 1

    def _populate_api_model_settings(self, card: Card, provider_settings: Dict[str, Any]) -> None:
        form = tk.Frame(card, bg=COLORS["bg_card"])
        form.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14))
        form.grid_columnconfigure(1, weight=1)

        row = self._populate_provider_readiness_banner(form, provider_settings, 0)
        labels = [
            ("Provider", self.api_provider_var),
            ("Base URL", self.api_base_url_var),
            ("API Key", self.api_key_var),
            ("主模型", self.main_model_var),
            ("模型搜索", self.model_search_var),
        ]
        for idx, (label, var) in enumerate(labels, start=row):
            tk.Label(form, text=label, bg=COLORS["bg_card"], fg=COLORS["text_sub"], font=FONTS["small"]).grid(row=idx, column=0, sticky="w", pady=5)
            if label == "Provider":
                widget = ttk.Combobox(form, textvariable=var, values=["openai_compatible", "deepseek", "qwen", "zhipu", "openai", "custom"], state="readonly")
            elif label == "API Key":
                widget = tk.Entry(form, textvariable=var, show="•", bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat")
            else:
                widget = tk.Entry(form, textvariable=var, bg=COLORS["bg_input"], fg=COLORS["text_main"], insertbackground=COLORS["text_main"], relief="flat")
            widget.grid(row=idx, column=1, sticky="ew", padx=(10, 0), pady=5, ipady=5)

        after_fields = row + len(labels)
        make_hint(
            form,
            "填写 Base URL 与 API Key 后保存；保存由 Runtime/本地桥接托管。前端立即清空明文输入框，只保留 configured、digest、错误码和审计号。留空 Key/Base URL 表示沿用 Runtime 已保存值。",
            bg=COLORS["bg_card"],
            wraplength=430,
        ).grid(row=after_fields, column=0, columnspan=2, sticky="ew", pady=(6, 4))

        model_box = tk.Listbox(form, height=5, bg=COLORS["bg_input"], fg=COLORS["text_main"], highlightbackground=COLORS["border_soft"], selectbackground=COLORS["accent"], relief="flat")
        model_box.grid(row=after_fields + 1, column=0, columnspan=2, sticky="ew", pady=(8, 6))
        for item in filter_model_catalog(self.model_search_var.get()):
            model_box.insert("end", f"{item.provider} · {item.model_id} · {item.display_name}")
        model_box.bind("<<ListboxSelect>>", lambda event, box=model_box: self._select_model_from_listbox(box))

        btns = tk.Frame(form, bg=COLORS["bg_card"])
        btns.grid(row=after_fields + 2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        tk.Button(btns, text="刷新模型", command=lambda: self.show_page("settings"), bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=12, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="保存 Provider", command=self._save_runtime_settings_frontend_only, bg=COLORS["accent"], fg="#FFFFFF", relief="flat", padx=12, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="检查状态", command=self._test_provider_config_frontend_only, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=12, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="配置模板", command=self._copy_provider_config_template_frontend_only, bg=COLORS["bg_card_2"], fg=COLORS["text_main"], relief="flat", padx=12, pady=5).pack(side="left")
        tk.Label(form, textvariable=self.settings_save_feedback_var, bg=COLORS["bg_card"], fg=COLORS["success"], font=FONTS["small_bold"], wraplength=430, justify="left").grid(row=after_fields + 3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        tk.Label(form, textvariable=self.settings_status_var, bg=COLORS["bg_card"], fg=COLORS["text_weak"], font=FONTS["small"], wraplength=430, justify="left").grid(row=after_fields + 4, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        tk.Button(form, text="配置文件位置说明", command=self._show_provider_path_hint, bg=COLORS["bg_card_2"], fg=COLORS["text_sub"], relief="flat", padx=10, pady=4).grid(row=after_fields + 5, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _copy_provider_config_template_frontend_only(self) -> None:
        template = {
            "schema": PROVIDER_CONFIG_SCHEMA_VERSION,
            "provider": safe_text(self.api_provider_var.get() or "openai_compatible", 40),
            "model": safe_text(self.main_model_var.get() or "deepseek-v4-pro", 100),
            "base_url": "<write-only-base-url>",
            "api_key": "<write-only-api-key>",
        }
        text = json.dumps(template, ensure_ascii=False, indent=2)
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.settings_status_var.set("已复制 Provider 配置模板到剪贴板；模板不包含真实 API Key 或 Base URL。")
        except tk.TclError as exc:
            self.settings_status_var.set(f"配置模板生成失败：{safe_text(exc, 160)}")

    def _show_provider_path_hint(self) -> None:
        self._show_safe_detail("Provider 配置位置", [
            self._provider_path_hint_text(),
            "",
            "本页保存 Provider 时，前端只提交写入请求；配置文件由 Runtime / 本地桥接落盘。",
            "导出报告、底部状态栏、首页会话信息均不得包含 API Key / Base URL 明文。",
        ])

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
                    allowed = {"provider", "model", "base_url_digest", "base_url_configured", "api_key_digest", "api_key_configured", "timeout", "stream", "planner_mode", "tool_execution_mode", "status", "provider_config_state", "config_error_code", "message", "audit_id", "requires_restart", "frontend_contract", "requested_backend_mode", "effective_backend_mode", "runtime_credential_persisted", "runtime_credential_store_digest", "provider_readiness", "readiness_label", "missing_fields", "next_action", "config_location_hint", "config_file_state", "config_file_exists", "config_path_digest", "local_bridge_can_persist", "raw_secret_visible_to_frontend", "last_provider_check_state", "last_provider_error_code", "last_provider_error_message", "last_provider_next_action", "last_provider_elapsed", "last_provider_audit_id"}
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
                            safe[safe_key] = safe_text(v, 180)
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
        after user intent is explicit; the helper owns manifest validation,
        rollback creation, allow/deny path checks, self-checks and rollback.
        """
        script = self._dataup_core_script()
        if not script.exists():
            self.dataup_status_var.set("DataUp 更新器缺失：scripts/dataup_update_core_l6717.py")
            return
        root = self._project_root()
        cmd = [sys.executable, str(script), "--root", str(root), *args]
        self.dataup_status_var.set(f"DataUp：{label} 已启动，等待更新器回执……")

        def worker() -> None:
            try:
                env = dict(**__import__("os").environ)
                env["PYTHONIOENCODING"] = "utf-8"
                proc = subprocess.run(cmd, cwd=str(root), env=env, text=True, capture_output=True, timeout=timeout)
                output = "\n".join(x for x in (proc.stdout, proc.stderr) if x).strip()
                summary = self._summarize_dataup_output(output, proc.returncode)
            except subprocess.TimeoutExpired:
                summary = f"DataUp：{label} 超时；未确认更新成功，请查看 reports/dataup_last_update_report_l6717.json。"
            except Exception as exc:
                summary = f"DataUp：{label} 启动失败：{safe_text(exc, 180)}"
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
                return f"DataUp：检查更新{'成功' if ok else '失败'}；source={source}；report={report}"
            plan = data.get("plan", {}) if isinstance(data.get("plan"), dict) else {}
            version = safe_text(plan.get("version", "未知版本"), 80)
            files = plan.get("file_count", 0)
            blocked = plan.get("blocked", [])
            if ok and stage == "applied":
                return f"DataUp：更新完成；version={version}；files={files}；已创建回滚点；请重启桌面端。report={report}"
            if ok:
                return f"DataUp：校验通过；stage={stage}；version={version}；files={files}；report={report}"
            if blocked:
                return f"DataUp：已阻断；stage={stage}；blocked={safe_text('；'.join(str(x) for x in blocked[:3]), 220)}；report={report}"
            return f"DataUp：执行失败；stage={stage}；returncode={returncode}；error={safe_text(data.get('error', ''), 180)}；report={report}"
        except Exception:
            tail = safe_text(output[-500:], 500) if output else "无输出"
            return f"DataUp：returncode={returncode}；输出摘要：{tail}"

    def _dataup_check_update(self) -> None:
        self._run_dataup_command(["--check", "--source", "auto"], label="检查更新", timeout=60)

    def _dataup_auto_update(self) -> None:
        approved = messagebox.askyesno(
            "DataUp 一键安全更新",
            "将从 Gitee 主源 / GitHub 备源读取 dataup/latest.json，下载 DataUp 包，并执行：manifest 校验、路径白名单、回滚点、自检、失败回滚。\n\n"
            "不会覆盖 Provider 配置、API Key、记忆、日志、审计私密数据或工作区。是否继续？",
        )
        if not approved:
            self.dataup_status_var.set("DataUp：用户取消一键安全更新。")
            return
        self._run_dataup_command(["--source", "auto", "--apply", "--yes"], label="一键安全更新", timeout=360)

    def _dataup_select_package(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 DataUp 更新包",
            filetypes=[("DataUp zip", "*.zip"), ("All files", "*.*")],
        )
        if not path:
            self.dataup_status_var.set("DataUp：未选择本地更新包。")
            return
        approved = messagebox.askyesno(
            "应用本地 DataUp 包",
            "将对所选 zip 执行 DataUp 安全更新流程：manifest 校验、路径白名单、回滚点、自检、失败回滚。\n\n是否继续？",
        )
        if not approved:
            self.dataup_status_var.set("DataUp：用户取消本地包更新。")
            return
        self._run_dataup_command(["--package", path, "--apply", "--yes"], label="本地包安全更新", timeout=360)

    def _show_dataup_boundary(self) -> None:
        self._show_safe_detail("DataUp 更新边界", [
            "一键更新按钮只启动 scripts/dataup_update_core_l6717.py，不由 Tk 前端直接复制或覆盖文件。",
            "允许覆盖：frontend/、desktop/、scripts/、docs/、reports/、launchers/、installer/updater/、01_启动入口/、dataup/ 与根目录说明文件。",
            "默认阻断：Provider 配置、API Key、.env、记忆、日志、审计私密数据、credentials、工作区私密数据、backend/runtime 核心路径。",
            "更新前创建 backups/dataup_rollback_YYYYMMDD_HHMMSS 回滚点。",
            "更新后执行 compileall、secret scan、desktop bundle preflight；失败则自动回滚。",
            "Gitee 主源：https://gitee.com/yu-yongxiang1994/natures-craftsmanship",
            "GitHub 备源：https://github.com/simahanfeng007-lgtm/Tian.Gong.Zao.Wu",
            "签名验签槽已预留；当前 stdlib 更新器执行 manifest sha256 校验，不把未实现的签名验真说成已完成。",
        ])

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
        tk.Checkbutton(btn_row, text="上传后自动进入 Runtime 文件处理", variable=self.file_auto_run_var, bg=COLORS["bg_card"], fg=COLORS["text_sub"], selectcolor=COLORS["bg_input"], activebackground=COLORS["bg_card"], activeforeground=COLORS["text_main"], relief="flat").pack(side="left", padx=(0, 8))
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
        make_hint(auth_body, "只读授权会选择输入文件；写入授权只选择输出目录/目标位置，不上传文件正文。两者都只生成授权 envelope：file_name、mode、scope、path_digest。", bg=COLORS["bg_card"], wraplength=760).grid(row=0, column=0, sticky="ew", pady=(0, 10))
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
            "blocked": "阻塞",
            "failed": "失败",
            "confirmation_required": "待确认",
            "recovered": "已恢复",
            "timeout": "超时",
        }.get(status, status)
