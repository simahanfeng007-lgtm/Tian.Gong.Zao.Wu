from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
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
from linyuanzhe_frontend.contracts.work_modes import (
    resolve_submit_work_mode, work_mode_label, work_mode_value, work_mode_spec,
)
from linyuanzhe_frontend.contracts.runtime_snapshot import ChatMessage, RuntimeSnapshot, StepSummary, CHAT_USER_INPUT_LIMIT, digest_text, safe_chat_text, safe_text, safe_path_setting_value
from linyuanzhe_frontend.version_info import PROVIDER_CONFIG_SCHEMA_VERSION
from .theme import COLORS, FONTS, STATUS_COLORS, THEME_PROFILES
from .localization import permission_mode_label, permission_mode_value, connector_kind_value, ui_text, host_access_scope_label, host_access_scope_value
from .widgets import Card, Chip, MetricRow, StepItem, LabeledValue, StatusPill, make_button, make_hint, make_readonly_banner, make_section_title


class FrontendActionsMixin:
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
            self._record_ui_warning("last_notice_error", exc, 120)

    def _sync_persona_text_widget(self) -> None:
        widget = getattr(self, "persona_prompt_text", None)
        if widget is None:
            return
        try:
            self.persona_prompt_var.set(safe_chat_text(widget.get("1.0", "end-1c"), 6000))
        except tk.TclError as exc:
            self._record_ui_warning("persona_prompt_sync", exc, 120)

    def _choose_host_access_root_frontend_only(self) -> None:
        """Choose a custom host-access root for Runtime-owned execution.

        UI only collects the path. Runtime / local bridge still owns permission,
        path normalization, and all actual file access.
        """
        try:
            initial = safe_path_setting_value(getattr(self, "host_access_root_var", tk.StringVar(value="")).get(), 520)
            selected = filedialog.askdirectory(title="选择自定义电脑访问根目录", initialdir=initial or str(Path.home()), parent=self)
            if not selected:
                return
            self.host_access_root_var.set(safe_path_setting_value(selected, 520))
            self.host_access_scope_var.set(host_access_scope_label("custom_root"))
            self._save_ui_preferences()
            self.settings_status_var.set("已选择自定义根目录；前端只保存设置，真实读取/写入仍由 Runtime 与 QualityGate 裁决。")
        except tk.TclError as exc:
            self._record_ui_warning("choose_host_access_root", exc, 120)

    def _is_api_key_placeholder(self, value: str) -> bool:
        text = str(value or "").strip()
        if not text:
            return False
        compact = text.replace("（已保存）", "").replace("(已保存)", "").replace(" ", "")
        return all(ch in {"•", "*", "·", "-"} for ch in compact) or text.startswith("<已保存") or "已保存" in text

    def _release_stream_guard(self, reason: str = "manual") -> None:
        with self._stream_lock:
            self._stream_worker = None
            self._stream_started_at = 0.0
        self._finish_live_stream_indicator("已解锁")
        self.stream_status_var.set(f"流式状态：已解除本地输入锁 · {safe_text(reason, 60)}")

    def _track_ime_input_event(self, event: tk.Event) -> None:
        """Guard CJK 输入法组合态：Enter 不应误触发提交。"""
        keysym = safe_text(getattr(event, "keysym", ""), 40)
        keycode = int(getattr(event, "keycode", 0) or 0)
        state = int(getattr(event, "state", 0) or 0)
        if keysym in {"Process", "Multi_key", "Hangul", "Kana_Lock", "Kanji"} or keycode == 229 or (state & 0x20000):
            self._ime_composition_guard_until = time.time() + 0.45

    def _is_ime_composing_event(self, event: tk.Event | None = None) -> bool:
        if time.time() < float(getattr(self, "_ime_composition_guard_until", 0.0) or 0.0):
            return True
        if event is None:
            return False
        keysym = safe_text(getattr(event, "keysym", ""), 40)
        keycode = int(getattr(event, "keycode", 0) or 0)
        return keysym in {"Process", "Multi_key", "Hangul", "Kana_Lock", "Kanji"} or keycode == 229

    def _copy_run_diagnostic(self) -> None:
        s = getattr(self, "snapshot", RuntimeSnapshot())
        lines = [
            "天工造物 v2.0 / 临渊者 · Run 工作台诊断",
            f"run_state={safe_text(getattr(s, 'run_workbench_state', ''), 60)} / {safe_text(getattr(s, 'run_status_label', ''), 60)}",
            f"run_id_digest={safe_text(getattr(s, 'active_run_id', ''), 120)}",
            f"task_id_digest={safe_text(getattr(s, 'active_task_id', ''), 120)}",
            f"frontend_work_mode={safe_text(getattr(s, 'frontend_work_mode', ''), 40)}",
            f"runtime_status={safe_text(getattr(s, 'runtime_status', ''), 120)}",
            f"connection_status={safe_text(getattr(s, 'connection_status', ''), 160)}",
            f"stream_status={safe_text(getattr(s, 'stream_status', ''), 80)}",
            f"current_task_status={safe_text(getattr(s, 'current_task_status', ''), 80)}",
            f"current_stage={safe_text(getattr(s, 'current_stage', ''), 180)}",
            f"current_tool={safe_text(getattr(s, 'current_tool_name', ''), 120)} / {safe_text(getattr(s, 'current_tool_status', ''), 120)}",
            f"last_event={safe_text(getattr(s, 'run_last_event', ''), 80)} at {safe_text(getattr(s, 'run_last_event_at', ''), 80)}",
            f"heartbeat={int(getattr(s, 'run_heartbeat_count', 0) or 0)} age_ms={int(getattr(s, 'run_heartbeat_age_ms', 0) or 0)}",
            f"planner_allowed={safe_text(getattr(s, 'planner_allowed', ''), 20)} tools_requested={safe_text(getattr(s, 'tools_requested', ''), 20)} quality_gate={safe_text(getattr(s, 'quality_gate_required', ''), 20)}",
            f"frontend_executes_tools={safe_text(getattr(s, 'frontend_executes_tools', False), 20)}",
            f"diagnostic={safe_text(getattr(s, 'run_diagnostic_summary', ''), 240)}",
        ]
        text = "\n".join(lines)
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._last_run_diagnostic_text = text
            self.stream_status_var.set("任务工作台：诊断已复制到剪贴板")
        except tk.TclError as exc:
            self._show_safe_detail("任务工作台诊断", lines + [f"剪贴板不可用：{safe_text(exc, 120)}"])

    def _mark_stream_worker_done(self, thread: threading.Thread | None = None) -> None:
        with self._stream_lock:
            if thread is None or self._stream_worker is thread:
                self._stream_worker = None
                self._stream_started_at = 0.0

    def _schedule_stream_guard_watchdog(self, thread: threading.Thread) -> None:
        timeout_ms = int(max(15.0, float(getattr(self, "_stream_soft_timeout_seconds", 900.0))) * 1000)
        try:
            self.after(timeout_ms, lambda t=thread: self._stream_guard_watchdog(t))
        except tk.TclError as exc:
            self._record_ui_warning("stream_guard_watchdog_schedule", exc, 120)

    def _stream_guard_watchdog(self, thread: threading.Thread) -> None:
        try:
            with self._stream_lock:
                active = self._stream_worker is thread and thread.is_alive()
                age = time.time() - float(getattr(self, "_stream_started_at", 0.0) or 0.0)
                if active and age >= float(getattr(self, "_stream_soft_timeout_seconds", 900.0)):
                    self._stream_worker = None
                    self._stream_started_at = 0.0
                else:
                    return
            self.stream_status_var.set("流式状态：本地输入锁已超时解除；原后台请求仍交由运行时收口。")
            self._finish_live_stream_indicator("已解锁")
        except tk.TclError as exc:
            self._record_ui_warning("stream_guard_watchdog", exc, 120)

    # ------------------------------------------------------------ work modes
    def _current_work_mode_value(self) -> str:
        return work_mode_value(getattr(self, "work_mode_var", tk.StringVar(value="聊天")).get())

    def _current_work_mode_label(self) -> str:
        return work_mode_label(self._current_work_mode_value())

    def _current_work_mode_button_text(self) -> str:
        return work_mode_spec(self._current_work_mode_value()).send_button

    def _on_work_mode_changed_frontend_only(self) -> None:
        mode = self._current_work_mode_value()
        spec = work_mode_spec(mode)
        try:
            self.work_mode_var.set(spec.label)
        except Exception:
            pass
        self._save_ui_preferences()
        if mode == "long_chain":
            self.stream_status_var.set(
                f"工作模式：{spec.label}。{spec.description} 任务流程可在设置页显示/隐藏；执行链仍归 Runtime / QualityGate。"
            )
        else:
            self.stream_status_var.set(
                f"工作模式：{spec.label}。普通聊天表面，不触发任务工作台、Planner 或工具链。"
            )
        try:
            # Rebuild lightweight chrome/input labels so the send button follows the selected mode.
            self._rebuild_shell_after_theme()
        except Exception as exc:
            self._record_ui_warning("work_mode_rebuild", exc, 120)

    def _resolve_submit_work_mode_payload(self, text: str) -> Dict[str, Any]:
        payload = resolve_submit_work_mode(self._current_work_mode_value(), text)
        if payload.get("mode") == "long_chain":
            self.stream_status_var.set("工作模式：已提交；允许 Runtime/Planner/ToolMode 真实执行。")
        else:
            self.stream_status_var.set("工作模式：普通聊天提交；不触发任务工作台、Planner 或工具链。")
        return payload


    def _normalize_base_url_entry(self, widget: tk.Entry | None = None) -> None:
        raw = safe_text(self.api_base_url_var.get(), 220).strip()
        if raw and not raw.startswith(("http://", "https://")):
            raw = "https://" + raw
            self.api_base_url_var.set(raw)
        ok = (not raw) or bool(raw.startswith("https://") and "." in raw.replace("https://", "", 1)) or raw.startswith("http://127.0.0.1") or raw.startswith("http://localhost")
        try:
            target = widget or getattr(self, "api_base_url_entry", None)
            if target is not None:
                target.configure(highlightthickness=1, highlightbackground=COLORS["border_soft"] if ok else COLORS["danger"], highlightcolor=COLORS["border_soft"] if ok else COLORS["danger"])
        except tk.TclError as exc:
            self._record_ui_warning("base_url_validate", exc, 80)
        if not ok:
            self.settings_status_var.set("Base URL 格式异常：建议填写 https://api.deepseek.com 或本地 loopback 地址。")

    def _mask_api_key_after_focus(self) -> None:
        text = safe_text(self.api_key_var.get(), 400).strip()
        if text and not self._is_api_key_placeholder(text):
            self._pending_api_key_plaintext = text
            if not self.api_key_visible_var.get():
                self.api_key_var.set("••••••••（已保存）")
        try:
            entry = getattr(self, "api_key_entry", None)
            if entry is not None:
                entry.configure(show="" if self.api_key_visible_var.get() else "•")
        except tk.TclError as exc:
            self._record_ui_warning("api_key_mask", exc, 80)

    def _toggle_api_key_visibility(self) -> None:
        self.api_key_visible_var.set(not bool(self.api_key_visible_var.get()))
        try:
            entry = getattr(self, "api_key_entry", None)
            if entry is not None:
                entry.configure(show="" if self.api_key_visible_var.get() else "•")
        except tk.TclError as exc:
            self._record_ui_warning("api_key_visibility", exc, 80)

    def _toggle_runtime_status_card(self) -> None:
        self.runtime_status_expanded = not bool(getattr(self, "runtime_status_expanded", False))
        self._save_ui_preferences()
        self.show_page("settings")

    def _toggle_config_file_card(self) -> None:
        self.config_panel_expanded = not bool(getattr(self, "config_panel_expanded", False))
        self._save_ui_preferences()
        self.show_page("settings")

    def _save_registry_toggle(self, kind: str, name: str) -> None:
        kind = safe_text(kind, 20)
        name = safe_text(name, 80)
        try:
            vars_map = getattr(self, "_registry_toggle_vars", {})
            disabled: list[str] = []
            prefix = f"{kind}:"
            for key, var in vars_map.items():
                if str(key).startswith(prefix) and not bool(var.get()):
                    disabled.append(str(key)[len(prefix):])
            self._ui_prefs_cache[f"disabled_{kind}s"] = sorted(set(disabled))
            self._save_ui_preferences()
            self.settings_status_var.set(f"{name}：已更新前端启用状态；真正工具/技能准入仍由 Runtime / ToolMode 裁决。")
        except Exception as exc:
            self._record_ui_warning("registry_toggle_save", exc, 120)

    def _reset_ui_preferences_frontend_only(self) -> None:
        if not messagebox.askyesno("重置默认", "确认重置前端外观与桌面偏好？不会删除运行时配置、密钥、审计或记忆。", parent=self):
            return
        try:
            path = self._ui_preferences_path()
            if path.exists():
                path.unlink()
        except Exception as exc:
            self._record_ui_warning("reset_ui_preferences", exc, 120)
        self.stream_status_var.set("已重置前端偏好；正在回到默认外观。")
        self._ui_prefs_cache = {}
        self.theme_profile_var.set("midnight")
        self.ui_font_family_var.set("system")
        self.chat_font_size_var.set(15)
        self.line_height_var.set(1.8)
        self.code_font_family_var.set("cascadia_code")
        self._apply_theme_selection()

    def _clear_chat_keyboard_shortcut(self) -> str:
        if not getattr(self, "_clear_confirm_armed", False):
            self._clear_confirm_armed = True
            self.stream_status_var.set("清屏确认：再次 Ctrl+L 将清空前端聊天转录。")
            try:
                self.after(2200, lambda: setattr(self, "_clear_confirm_armed", False))
            except tk.TclError as exc:
                self._record_ui_warning("clear_shortcut_after", exc, 80)
            return "break"
        self._clear_confirm_armed = False
        self._clear_chat_view_frontend_only()
        return "break"

    def _escape_key_dispatch(self) -> str:
        try:
            focus = self.focus_get()
            if focus is not None and isinstance(focus, tk.Toplevel):
                focus.destroy()
                return "break"
        except tk.TclError:
            pass
        self._request_task_interrupt()
        return "break"

    def _copy_last_assistant_reply(self) -> str:
        try:
            for msg in reversed(list(getattr(self.snapshot, "chat_messages", []) or [])):
                if safe_text(getattr(msg, "role", ""), 32).lower() not in {"user", "human"}:
                    text = safe_chat_text(getattr(msg, "text", ""), 8000)
                    self.clipboard_clear(); self.clipboard_append(text)
                    self.stream_status_var.set("已复制最后一条 AI 回复。")
                    return "break"
            self.stream_status_var.set("没有可复制的 AI 回复。")
        except tk.TclError as exc:
            self._record_ui_warning("copy_last_ai", exc, 120)
        return "break"

    def _approve_permission_once(self, ticket_id: str) -> None:
        self._submit_action_guard_decision(ticket_id, "approve")

    def _approve_permission_session(self, ticket_id: str) -> None:
        self._submit_action_guard_decision(ticket_id, "approve_session")

    def _reject_permission(self, ticket_id: str) -> None:
        self._submit_action_guard_decision(ticket_id, "reject")

    def _show_observability_detail(self) -> None:
        s = self.snapshot
        stats = dict(getattr(s, "trace_stats", {}) or {})
        lines = [
            f"契约：{safe_text(getattr(s, 'observability_contract', ''), 100)}",
            f"事件总数：{stats.get('total_events', len(getattr(s, 'trace_records', []) or []))}",
            f"工具事件：{stats.get('tool_events', 0)}",
            f"质量门事件：{stats.get('quality_gate_events', 0)}",
            f"错误事件：{stats.get('error_events', 0)}",
            f"收口顺序有效：{getattr(s, 'trace_terminal_order_valid', True)}",
            f"导出摘要指纹：{safe_text(getattr(s, 'trace_export_digest', ''), 40) or '待生成'}",
            "",
            "最近轨迹：",
        ]
        for rec in list(getattr(s, "trace_records", []) or [])[-20:]:
            lines.append(f"- #{getattr(rec, 'seq', '')} {getattr(rec, 'category', '')}/{getattr(rec, 'source_event', '')} · {getattr(rec, 'phase', '')} · {getattr(rec, 'message', '')}")
        lines.append("")
        lines.append("边界：此详情只读展示脱敏轨迹，不导出原始提示词、密钥、端点、路径或工具参数。")
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
            "边界：此处只展示质量门脱敏摘要。允许/拒绝/修改只会提交 运行时请求，前端不直接放行工具。",
        ]
        self._show_safe_detail("质量门详情（脱敏摘要）", lines)

    def _show_audit_detail(self) -> None:
        s = self.snapshot
        lines = [
            f"审计数量：{s.audit_count}",
            f"证据引用：{s.证据引用}",
            "",
            "边界：FE.01 只展示 证据引用 与审计数量，不展开完整审计链、prompt、密钥或真实路径；前端不写审计。",
        ]
        self._show_safe_detail("审计摘要（脱敏）", lines)

    def _show_recovery_detail(self) -> None:
        s = self.snapshot
        actions = s.recovery_next_actions or ["暂无下一步恢复动作。"]
        lines = [
            f"恢复票据：{s.recovery_ticket_id or '无'}",
            f"失败次数：{s.recovery_failure_count}",
            f"续接方案数：{s.recovery_resume_plan_count}",
            f"需要人工确认：{'是' if s.recovery_requires_human_confirmation else '否'}",
            "",
            "下一步动作：",
            *[f"- {item}" for item in actions],
            "",
            "边界：恢复续接按钮只展示摘要，不触发恢复执行。",
        ]
        self._show_safe_detail("恢复续接详情（占位）", lines)

    def _show_hook_detail(self) -> None:
        s = self.snapshot
        stats = dict(getattr(s, "hook_stats", {}) or {})
        lines = [
            "L6.63 规则总线确定性规则层：",
            f"契约：{getattr(s, 'hook_bus_contract', '')}",
            f"规则启用：{getattr(s, 'hook_enabled', True)}",
            f"规则数量：{stats.get('total_hooks', 0)}",
            f"允许/警告/阻断：{stats.get('allow_count', 0)} / {stats.get('warn_count', 0)} / {stats.get('block_count', 0)}",
            f"最近规则：{safe_text(stats.get('last_rule_id', ''), 100)}",
            f"最近阻断：{safe_text(getattr(s, 'hook_last_blocker', '') or stats.get('last_blocker', ''), 220) or '无'}",
            f"摘要指纹：{safe_text(getattr(s, 'hook_export_digest', ''), 32) or '待生成'}",
            "",
            "边界：",
            "- 规则总线只校验请求/事件，不执行命令。",
            "- 模型服务、工具、长期记忆、审计、回滚仍只能由运行时 / 天工网关管控。",
            "- A5 被错误放行、运行收口事件早于最终回复事件、缺安全标记的请求会被确定性阻断。",
            "",
            "最近记录：",
        ]
        for rec in list(getattr(s, "hook_records", []) or [])[-20:]:
            lines.append(f"#{getattr(rec, 'seq', '')} {getattr(rec, 'stage', '')} · {getattr(rec, 'rule_id', '')} · {getattr(rec, 'verdict', '')} · {getattr(rec, 'reason', '')}")
        self._show_safe_detail("规则总线详情", lines)

    def _show_boundary_detail(self) -> None:
        lines = [
            "前端安全边界：",
            "- 真实运行时只通过 /chat/stream-events 连接",
            "- 智能体界面事件只用于渲染，不作为前端命令",
            "- 质量门行动守卫卡只允许提交请求，不直接放行",
            "- 审计/回滚卡片只读显示，前端不写审计、不应用回滚",
            "- 流式输出采用 45ms 合并与虚拟长对话渲染",
            "- 规则总线对会话、模型配置、确认、控制、事件、收口做确定性请求守卫",
            "- 中断/停止/复位只向运行时发送请求，不由前端执行",
            "- 文件传输只提交脱敏传输请求，不在前端执行工具或写审计",
            "- 对话引导只填入输入栏，仍由用户确认发送，不替代规划器",
            "- 模型服务设置只向运行时 /settings/provider 提交写入请求，界面只显示已配置/摘要指纹/错误态",
            "- 不调用适配器",
            "- 不直接执行工具",
            "- 不裸调模型或模型服务开发包",
            "- 不写 tiangong_kernel",
            "- 不裸写长期记忆或审计",
            "- 不直接应用回滚或自我迭代合入",
            "- 未配置模型接口时只提示进入设置页，不输出演示回答",
        ]
        self._show_safe_detail("FE.01 安全边界", lines)

    def _refresh_snapshot_frontend_only(self) -> None:
        try:
            refresh = getattr(self.client, "refresh_snapshot", None)
            self.snapshot = refresh() if callable(refresh) else self.client.get_snapshot()
            self.stream_status_var.set("刷新完成：已读取运行时客户端脱敏快照")
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

    # ------------------------------------------------------------ local history
    def _persist_current_chat_history(self, snapshot: RuntimeSnapshot | None = None) -> None:
        snap = snapshot or getattr(self, "snapshot", None)
        if snap is None:
            return
        if bool(getattr(self, "_history_readonly_mode", False)) or safe_text(getattr(snap, "source_kind", ""), 80) == "local_history_readonly":
            # L6.72.49：历史页是只读回放，不写新历史、不触发记忆、不提交工具。
            return
        try:
            payload = self.history_store.snapshot_to_payload(snap)
            digest = self.history_store.payload_digest(payload)
            if digest == getattr(self, "_last_history_save_digest", ""):
                return
            path = self.history_store.save_snapshot(snap)
            if path is not None:
                self._last_history_save_digest = digest
        except Exception as exc:
            self._record_ui_warning("local_history_persist", exc, 160)

    def _restore_last_local_session_if_requested(self) -> None:
        if not bool(getattr(self, "restore_last_session_var", tk.BooleanVar(value=True)).get()):
            return
        try:
            if list(getattr(self.snapshot, "chat_messages", []) or []):
                return
            records = self.history_store.list_records(limit=1)
            if not records:
                return
            payload = self.history_store.read_session(records[0].session_id)
            messages = [ChatMessage.from_mapping(item) for item in list(payload.get("messages", []) or [])]
            if not messages:
                return
            self.snapshot.session_id = safe_text(payload.get("session_id", self.snapshot.session_id), 120)
            self.snapshot.chat_messages = messages
            self.snapshot.visible_message_count = len(messages)
            self.snapshot.hidden_message_count = 0
            self.snapshot.current_stage = "已恢复上次本地会话状态"
            self.snapshot.current_task_status = "READY"
            self._history_loaded_payload = payload
        except Exception as exc:
            self._record_ui_warning("local_history_restore", exc, 160)

    def _select_local_history(self, session_id: str) -> None:
        self.selected_history_session_id = safe_text(session_id, 120)
        self.stream_status_var.set(f"历史：已选中本地会话 {safe_text(session_id, 48)}")

    def _load_local_history_readonly(self, session_id: str = "") -> None:
        sid = safe_text(session_id or getattr(self, "selected_history_session_id", ""), 120)
        if not sid:
            self._show_frontend_notice("未选择历史", "请先选择一条本地历史记录。")
            return
        try:
            payload = self.history_store.read_session(sid)
            if not payload:
                self._show_frontend_notice("历史不存在", "未找到这条本地历史记录；可能已被清理。")
                return
            messages = [ChatMessage.from_mapping(item) for item in list(payload.get("messages", []) or [])]
            self.snapshot.session_id = safe_text(payload.get("session_id", sid), 120)
            self.snapshot.chat_messages = messages
            self.snapshot.visible_message_count = len(messages)
            self.snapshot.hidden_message_count = 0
            self.snapshot.source_kind = "local_history_readonly"
            self.snapshot.current_stage = "本地历史只读回放"
            self.snapshot.current_task_status = "READONLY"
            self._history_loaded_payload = payload
            self._history_readonly_mode = True
            self.stream_status_var.set("历史：已加载到聊天区，只读回放；新会话后才可继续对话。")
            self.show_page("chat")
        except Exception as exc:
            self._show_frontend_notice("历史读取失败", f"读取本地历史失败：{safe_text(exc, 180)}")

    def _request_history_search(self) -> None:
        self.show_page("history")

    def _export_selected_history(self, fmt: str = "md") -> None:
        sid = safe_text(getattr(self, "selected_history_session_id", ""), 120)
        if not sid:
            records = self.history_store.list_records(self.history_search_var.get(), limit=1)
            sid = records[0].session_id if records else ""
        if not sid:
            self._show_frontend_notice("没有可导出的历史", "当前没有选中的本地历史记录。")
            return
        try:
            default_dir = self.history_store.root.parent / "exports"
            target = filedialog.askdirectory(title="选择导出目录", initialdir=str(default_dir))
            if not target:
                return
            path = self.history_store.export_session(sid, fmt, Path(target))
            self.stream_status_var.set(f"历史导出：{path.name}")
            self._show_frontend_notice("导出完成", f"已导出本地历史：{path.name}")
        except tk.TclError as exc:
            self._show_frontend_notice("导出不可用", f"当前环境无法打开目录选择器：{safe_text(exc, 160)}")
        except Exception as exc:
            self._show_frontend_notice("导出失败", f"导出本地历史失败：{safe_text(exc, 180)}")

    def _export_current_conversation(self, fmt: str = "md") -> None:
        try:
            self._persist_current_chat_history(getattr(self, "snapshot", None))
            sid = safe_text(getattr(self.snapshot, "session_id", ""), 120)
            if not sid:
                self._show_frontend_notice("无法导出", "当前会话缺少 session_id。")
                return
            target = filedialog.askdirectory(title="选择导出目录", initialdir=str(self.history_store.root.parent / "exports"))
            if not target:
                return
            path = self.history_store.export_session(sid, fmt, Path(target))
            self.stream_status_var.set(f"当前会话导出：{path.name}")
            self._show_frontend_notice("导出完成", f"当前会话已导出：{path.name}")
        except tk.TclError as exc:
            self._show_frontend_notice("导出不可用", f"当前环境无法打开目录选择器：{safe_text(exc, 160)}")
        except Exception as exc:
            self._show_frontend_notice("导出失败", f"当前会话导出失败：{safe_text(exc, 180)}")

    def _provider_model_values_frontend_only(self, provider: str | None = None) -> List[str]:
        return model_values_for_provider(provider or self.api_provider_var.get(), self.model_search_var.get(), include_custom=True)

    def _effective_model_for_submit_frontend_only(self) -> str:
        return effective_model_name(self.api_provider_var.get(), self.main_model_var.get(), getattr(self, "custom_model_var", tk.StringVar(value="")).get())

    def _refresh_provider_model_controls_frontend_only(self, *, reset_model: bool = False, fill_base_url: bool = False) -> None:
        provider = normalize_provider_value(self.api_provider_var.get())
        if provider != self.api_provider_var.get():
            self.api_provider_var.set(provider)
            return
        values = self._provider_model_values_frontend_only(provider)
        combo = getattr(self, "provider_model_combobox", None)
        if combo is not None:
            try:
                combo.configure(values=values, state="readonly")
            except tk.TclError as exc:
                self._record_ui_warning("provider_model_combo_refresh", exc, 100)
        current = safe_text(self.main_model_var.get(), 120)
        if reset_model or current not in values:
            self.main_model_var.set(default_model_for_provider(provider) or (values[0] if values else MODEL_CUSTOM_SENTINEL))
        custom_entry = getattr(self, "custom_model_entry", None)
        custom_allowed = provider_allows_custom_model(provider)
        try:
            if custom_entry is not None:
                custom_entry.configure(state="normal" if custom_allowed else "disabled")
        except tk.TclError as exc:
            self._record_ui_warning("custom_model_entry_refresh", exc, 100)
        default_base = default_base_url_for_provider(provider)
        if fill_base_url and default_base:
            raw_base = safe_text(self.api_base_url_var.get(), 220).strip()
            old_default = default_base_url_for_provider(getattr(self, "_last_api_provider", ""))
            if not raw_base or raw_base == old_default:
                self.api_base_url_var.set(default_base)
        hint = (
            f"模型联动：服务商={provider_display_name(provider)}；"
            f"可选模型={len(values)} 个；"
            f"自定义模型={'允许' if custom_allowed else '不允许'}。"
            "OpenAI / 兼容网关 / 本地模型可直接填写最新或私有模型名。"
        )
        self.settings_status_var.set(hint)

    def _on_provider_changed_frontend_only(self) -> None:
        if bool(getattr(self, "_provider_trace_guard", False)):
            return
        self._provider_trace_guard = True
        try:
            provider = normalize_provider_value(self.api_provider_var.get())
            previous = getattr(self, "_last_api_provider", provider)
            if provider != self.api_provider_var.get():
                self.api_provider_var.set(provider)
            self._refresh_provider_model_controls_frontend_only(reset_model=(provider != previous), fill_base_url=True)
            self._last_api_provider = provider
        finally:
            self._provider_trace_guard = False

    def _on_model_selected_frontend_only(self, _event: tk.Event | None = None) -> None:
        provider = normalize_provider_value(self.api_provider_var.get())
        selected = safe_text(self.main_model_var.get(), 120)
        if selected == MODEL_CUSTOM_SENTINEL:
            self.settings_status_var.set(f"{provider_display_name(provider)}：请输入自定义模型名称；保存时会提交该模型名。")
        else:
            self.settings_status_var.set(f"已选择 {provider_display_name(provider)} / {selected}；前端未调用模型服务。")

    def _clear_local_data_frontend_only(self) -> None:
        if not messagebox.askyesno("清除本地数据", "确认清除本地对话历史与前端缓存？不会删除运行时审计、长期记忆或项目源码。", parent=self):
            return
        if not messagebox.askyesno("二次确认", "此操作会删除 workspace/chat_history 下的本地历史文件。确认继续？", parent=self):
            return
        try:
            count = self.history_store.clear_all()
            self._last_history_save_digest = ""
            self._history_loaded_payload = {}
            self.selected_history_session_id = ""
            self.stream_status_var.set(f"本地数据：已清除 {count} 条历史记录与前端缓存。")
            self.show_page(self.current_page if self.current_page != "history" else "settings")
        except Exception as exc:
            self._show_frontend_notice("清理失败", f"清理本地数据失败：{safe_text(exc, 180)}")

    def _select_model_from_listbox(self, box: tk.Listbox) -> None:
        selection = box.curselection()
        if not selection:
            return
        raw = safe_text(box.get(selection[0]), 240)
        parts = [part.strip() for part in raw.split("·")]
        if len(parts) >= 2:
            provider = normalize_provider_value(parts[0])
            model = safe_text(parts[1], 120)
            self.api_provider_var.set(provider)
            values = self._provider_model_values_frontend_only(provider)
            self.main_model_var.set(model if model in values else MODEL_CUSTOM_SENTINEL)
            if model not in values:
                self.custom_model_var.set(model)
            self._refresh_provider_model_controls_frontend_only(reset_model=False, fill_base_url=True)
            self.settings_status_var.set(f"已选择模型：{provider_display_name(provider)} / {model}。仅更新前端设置表单，未调用模型服务。")

    def _save_runtime_settings_frontend_only(self) -> None:
        self._sync_persona_text_widget()
        self._normalize_base_url_entry(None)
        api_key_input = self.api_key_var.get()
        pending_plain = safe_text(getattr(self, "_pending_api_key_plaintext", ""), 400)
        api_key_for_submit = pending_plain if self._is_api_key_placeholder(api_key_input) and pending_plain else ("" if self._is_api_key_placeholder(api_key_input) else api_key_input)
        tool_mode_raw = permission_mode_value(self.tool_execution_mode_var.get())
        effective_model = self._effective_model_for_submit_frontend_only()
        raw_settings = {
            "provider": normalize_provider_value(self.api_provider_var.get()),
            "main_model": effective_model,
            "model": effective_model,
            "selected_model": self.main_model_var.get(),
            "custom_model": self.custom_model_var.get(),
            "api_base_url": self.api_base_url_var.get(),
            "base_url": self.api_base_url_var.get(),
            "api_key": api_key_for_submit,
            "tool_execution_mode": tool_mode_raw,
            "host_access_scope": host_access_scope_value(getattr(self, "host_access_scope_var", tk.StringVar(value="system_drive")).get()),
            "host_access_root": safe_path_setting_value(getattr(self, "host_access_root_var", tk.StringVar(value="")).get(), 520),
            "persona_name": self.persona_name_var.get(),
            "persona_prompt": self.persona_prompt_var.get(),
        }
        settings = sanitize_runtime_settings(raw_settings)
        self._sanitized_settings = settings
        submitter = getattr(self.client, "submit_provider_settings", None)
        result: Dict[str, Any] = {}
        if callable(submitter):
            try:
                result = submitter(raw_settings) or {}
                state = safe_text(result.get("status") or result.get("provider_config_state") or "submitted", 40)
                message = safe_text(result.get("message") or "运行时模型服务设置请求已提交。", 220)
                self.settings_status_var.set(
                    "运行时回执："
                    f"状态={state}；服务商={safe_text(result.get('provider') or settings['provider'], 40)}；"
                    f"模型={safe_text(result.get('model') or settings['main_model'], 80)}；"
                    f"权限模式={safe_text(result.get('tool_execution_mode') or settings.get('tool_execution_mode'), 40)}；"
                    f"电脑访问={host_access_scope_label(result.get('host_access_scope') or settings.get('host_access_scope'))}；"
                    f"本体={safe_text(result.get('persona_name') or settings.get('persona_name'), 32)}；"
                    f"接口密钥已配置={result.get('api_key_configured', settings['api_key_configured'])}；"
                    f"密钥摘要指纹={safe_text(result.get('api_key_digest') or settings['api_key_digest'] or '无', 32)}；"
                    f"服务地址已配置={result.get('base_url_configured', settings['base_url_configured'])}；"
                    f"服务地址摘要指纹={safe_text(result.get('base_url_digest') or settings['base_url_digest'] or '无', 32)}；"
                    f"错误={safe_text(result.get('config_error_code') or '无', 80)}；"
                    f"审计={safe_text(result.get('audit_id') or '无', 80)}。{message}"
                )
                try:
                    refresh = getattr(self.client, "refresh_snapshot", None)
                    self.snapshot = refresh() if callable(refresh) else self.client.get_snapshot()
                except Exception as exc:
                    self._record_ui_warning("last_snapshot_after_provider_save_error", exc, 120)
            except Exception as exc:
                self.settings_status_var.set(
                    "运行时模型服务设置提交失败："
                    f"服务商={settings['provider']}；模型={settings['main_model']}；"
                    f"权限模式={settings.get('tool_execution_mode')}；电脑访问={host_access_scope_label(settings.get('host_access_scope'))}；本体={settings.get('persona_name')}；"
                    f"接口密钥已配置={settings['api_key_configured']}；密钥摘要指纹={settings['api_key_digest'] or '无'}；"
                    f"服务地址已配置={settings['base_url_configured']}；服务地址摘要指纹={settings['base_url_digest'] or '无'}；"
                    f"错误={safe_text(exc, 160)}。未调用模型服务，未写入前端持久层。"
                )
        else:
            self.settings_status_var.set(
                "已保存前端脱敏设置摘要："
                f"服务商={settings['provider']}；模型={settings['main_model']}；"
                f"权限模式={settings.get('tool_execution_mode')}；电脑访问={host_access_scope_label(settings.get('host_access_scope'))}；本体={settings.get('persona_name')}；"
                f"接口密钥已配置={settings['api_key_configured']}；密钥摘要指纹={settings['api_key_digest'] or '无'}；"
                f"服务地址已配置={settings['base_url_configured']}；服务地址摘要指纹={settings['base_url_digest'] or '无'}。"
                "当前运行时客户端不支持 /settings/provider 写入；未调用模型服务，未写入运行时。"
            )
        self.tool_execution_mode_var.set(permission_mode_label(settings.get("tool_execution_mode", tool_mode_raw)))
        try:
            self.host_access_scope_var.set(host_access_scope_label(result.get("host_access_scope") or settings.get("host_access_scope") or self.host_access_scope_var.get()))
        except Exception:
            pass
        self._save_ui_preferences()
        display_base = safe_text(result.get("base_url_display") or raw_settings.get("api_base_url") or self.api_base_url_var.get(), 220)
        if display_base:
            self.api_base_url_var.set(display_base)
        self._save_ui_preferences()
        key_configured = bool(result.get("api_key_configured", settings.get("api_key_configured")))
        if key_configured or api_key_for_submit:
            self.api_key_var.set("••••••••（已保存）")
            self._pending_api_key_plaintext = ""
        self._flash_settings_save_feedback("✓ 已保存：服务地址完整保留显示；接口密钥只显示已配置；模式、权限、电脑访问范围与 Soul 已写入设置。")
        self._rebuild_shell_after_theme()

    def _flash_settings_save_feedback(self, message: str = "✓ 已保存") -> None:
        self.settings_save_feedback_var.set(safe_text(message, 80))
        after_id = getattr(self, "_settings_feedback_after_id", None)
        if after_id:
            try:
                self.after_cancel(after_id)
            except tk.TclError as exc:
                self._record_ui_warning("settings_feedback_cancel", exc, 120)
        try:
            self._settings_feedback_after_id = self.after(2000, lambda: self.settings_save_feedback_var.set(""))
        except tk.TclError as exc:
            self._record_ui_warning("settings_feedback_schedule", exc, 120)

    def _test_provider_config_frontend_only(self) -> None:
        """Read the public 模型服务投影 without calling the 模型服务开发包."""
        provider_settings = self._get_provider_settings_public()
        readiness = self._provider_readiness_public(provider_settings)
        state = safe_text(provider_settings.get("status") or provider_settings.get("provider_config_state") or "未读取", 40)
        mode = safe_text(provider_settings.get("effective_backend_mode") or provider_settings.get("requested_backend_mode") or readiness.get("effective_backend_mode") or "未读取", 40)
        key_ok = bool(provider_settings.get("api_key_configured"))
        base_ok = bool(provider_settings.get("base_url_configured"))
        key_digest = safe_text(provider_settings.get("api_key_digest") or "无", 32)
        base_digest = safe_text(provider_settings.get("base_url_digest") or "无", 32)
        last_check = safe_text(provider_settings.get("last_provider_check_state") or "not_tested", 60)
        last_error = safe_text(provider_settings.get("last_provider_error_code") or readiness.get("config_error_code") or "无", 80)
        last_next = safe_text(provider_settings.get("last_provider_next_action") or readiness.get("primary_action", "刷新快照"), 120)
        self.settings_status_var.set(
            f"配置检查：{safe_text(readiness.get('label', '未知'), 40)}；状态={state}；模式={ui_text(mode)}；"
            f"接口密钥已配置={key_ok}；密钥摘要指纹={key_digest}；"
            f"服务地址已配置={base_ok}；服务地址摘要指纹={base_digest}；"
            f"最近联调={ui_text(last_check)}；最近错误={ui_text(last_error)}；"
            f"下一步={last_next}。"
            "此检查只读模型服务配置端点，不裸调模型服务；真实联调由会话发送链路触发。"
        )

    def _submit_iteration_confirmation(self, candidate_id: str, decision: str) -> None:
        submit = getattr(self.client, "submit_self_iteration_confirmation", None)
        if callable(submit):
            self.snapshot = submit(candidate_id, decision)
        else:
            self.snapshot.submit_self_iteration_confirmation(candidate_id, decision)
        self.stream_status_var.set(f"自我迭代确认：{safe_text(decision, 32)}")
        self.show_page("iteration")

    def _send_message_from_event(self, _event: tk.Event) -> str:
        if self._is_ime_composing_event(_event):
            self.stream_status_var.set("输入法组合中：已阻止 Enter 误发送")
            return "break"
        self._send_message()
        return "break"

    def _insert_newline_from_event(self, event: tk.Event) -> str:
        widget = event.widget
        try:
            widget.insert("insert", "\n")
        except Exception as exc:
            self._record_ui_warning("last_input_error", exc, 120)
        return "break"

    def _send_message(self) -> None:
        if bool(getattr(self, "_history_readonly_mode", False)):
            self._show_frontend_notice("历史只读", "当前正在查看本地历史回放。请点击“新会话”后再继续对话。")
            return
        if hasattr(self, "input_text"):
            text = self.input_text.get("1.0", "end-1c").strip()
        else:
            text = getattr(self, "input_var", tk.StringVar()).get().strip()
        if not text:
            self._show_frontend_notice("输入为空", "请输入消息；空输入不会提交到运行时。")
            return
        status_probe = getattr(self.client, "try_handle_status_probe", None)
        if callable(status_probe):
            try:
                local_snapshot = status_probe(text)
            except Exception as exc:
                self._record_ui_warning("status_probe_local_reply", exc, 120)
                local_snapshot = None
            if local_snapshot is not None:
                self.snapshot = local_snapshot
                self.stream_status_var.set("流式状态：已显示当前任务状态")
                self._finish_live_stream_indicator("状态已更新")
                if hasattr(self, "input_text"):
                    try:
                        self.input_text.delete("1.0", "end")
                        self.input_text.focus_set()
                        self._sync_input_placeholder()
                    except tk.TclError as exc:
                        self._record_ui_warning("status_probe_input_clear", exc, 120)
                if self.current_page == "chat":
                    if not self._render_live_chat_transcript(local_snapshot):
                        self.show_page("chat")
                    self._render_statusbar(local_snapshot)
                else:
                    self.show_page("chat")
                return
        work_payload = self._resolve_submit_work_mode_payload(text)
        mode_label = safe_text(work_payload.get("label", "聊天"), 24)
        status = "流式状态：工作模式提交中 · 请求 Runtime 执行链" if work_payload.get("long_chain_requested") else "流式状态：聊天提交中"
        started = self._submit_text_to_runtime_stream(text, status=status, work_mode_payload=work_payload)
        if started and hasattr(self, "input_text"):
            try:
                self.input_text.delete("1.0", "end")
                self.input_text.focus_set()
                self._sync_input_placeholder()
            except tk.TclError as exc:
                self._record_ui_warning("send_input_clear", exc, 120)

    def _clear_chat_view_frontend_only(self) -> None:
        self._release_stream_guard("clear_chat")
        clearer = getattr(self.client, "clear_local_transcript", None)
        if callable(clearer):
            try:
                self.snapshot = clearer()
            except Exception as exc:
                self._record_ui_warning("chat_clear_client_transcript", exc, 120)
        else:
            try:
                self.snapshot.chat_messages = []
                self.snapshot.visible_message_count = 0
                self.snapshot.hidden_message_count = 0
            except Exception as exc:
                self._record_ui_warning("chat_clear_snapshot_transcript", exc, 120)
        body = getattr(self, "_chat_body_widget", None)
        try:
            if body is not None and body.winfo_exists():
                body.configure(state="normal")
                body.delete("1.0", "end")
                body.configure(state="disabled")
            self._chat_render_signatures = []
            self.stream_status_var.set("清屏完成：已清除前端转录缓存；不删除运行时审计、记忆或任务记录。")
        except tk.TclError as exc:
            self._record_ui_warning("chat_clear_frontend_only", exc, 120)

    def _apply_deepseek_v4_preset_frontend_only(self) -> None:
        self.api_provider_var.set("deepseek")
        self.api_base_url_var.set(default_base_url_for_provider("deepseek"))
        self.main_model_var.set("deepseek-v4-pro")
        self.custom_model_var.set("")
        self.model_search_var.set("deepseek")
        self._refresh_provider_model_controls_frontend_only(reset_model=False, fill_base_url=False)
        self._save_ui_preferences()
        self.settings_status_var.set("已填入 DeepSeek V4 模板：服务地址=https://api.deepseek.com，模型=deepseek-v4-pro。点击“保存全部设置”后，发一条短消息复测。")

    def _submit_text_to_runtime_stream(self, text: str, *, status: str = "流式状态：提交中", work_mode_payload: Dict[str, Any] | None = None) -> bool:
        text = safe_chat_text(text, CHAT_USER_INPUT_LIMIT).strip()
        if not text:
            return False
        now = time.time()
        with self._stream_lock:
            worker = self._stream_worker
            if worker is not None and worker.is_alive():
                age = now - float(getattr(self, "_stream_started_at", 0.0) or 0.0)
                if age < float(getattr(self, "_stream_soft_timeout_seconds", 900.0)):
                    self.stream_status_var.set("流式状态：上一条仍在收口；可点 停止/复位/新会话 解除本地输入锁。")
                    self._finish_live_stream_indicator("等待收口")
                    return False
                self._stream_worker = None
                self._stream_started_at = 0.0
                self.stream_status_var.set("流式状态：已自动解除超时输入锁，允许继续提交。")
        self.stream_status_var.set(status)
        self._start_live_stream_indicator("正在思考")
        work_mode_payload = work_mode_payload or self._resolve_submit_work_mode_payload(text)
        submit_stream = getattr(self.client, "submit_user_message_streaming", None)
        if not callable(submit_stream):
            try:
                self.snapshot = self.client.submit_user_message(text, work_mode_payload=work_mode_payload)  # type: ignore[arg-type]
            except TypeError:
                self.snapshot = self.client.submit_user_message(text)
            if self.current_page == "chat":
                if not self._render_live_chat_transcript(self.snapshot):
                    self.show_page("chat")
                self._render_statusbar(self.snapshot)
                self.stream_status_var.set("流式状态：completed")
                self._finish_live_stream_indicator("已完成")
                try:
                    if hasattr(self, "input_text"):
                        self.input_text.focus_set()
                except tk.TclError as exc:
                    self._record_ui_warning("sync_submit_focus", exc, 120)
            else:
                self.show_page("chat")
            return True

        def on_snapshot(snapshot: RuntimeSnapshot) -> None:
            self._post_to_ui(lambda snap=snapshot: self._queue_stream_snapshot(snap))

        def worker() -> None:
            thread = threading.current_thread()
            try:
                snapshot = submit_stream(text, on_snapshot=on_snapshot, work_mode_payload=work_mode_payload)
                self._post_to_ui(lambda snap=snapshot: self._queue_stream_snapshot(snap, finished=True, force=True))
            except Exception as exc:
                self._post_to_ui(lambda err=exc: self._stream_failed(err))
            finally:
                self._post_to_ui(lambda th=thread: self._mark_stream_worker_done(th))

        t = threading.Thread(target=worker, name="linyuanzhe-runtime-sse-stream", daemon=True)
        with self._stream_lock:
            self._stream_worker = t
            self._stream_started_at = time.time()
        t.start()
        self._schedule_stream_guard_watchdog(t)
        return True

    def _queue_stream_snapshot(self, snapshot: RuntimeSnapshot, *, finished: bool = False, force: bool = False) -> None:
        self._pending_stream_snapshot = snapshot
        self._pending_stream_finished = self._pending_stream_finished or finished
        if force or finished or self._render_scheduler.should_render(force=False):
            if self._render_after_id is not None:
                try:
                    self.after_cancel(self._render_after_id)
                except tk.TclError as exc:
                    self._record_ui_warning("last_render_cancel_error", exc, 120)
                self._render_after_id = None
            self._flush_pending_stream_snapshot()
            return
        if self._render_after_id is None:
            self._render_after_id = self.after(self._render_scheduler.min_interval_ms, self._flush_pending_stream_snapshot)

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
        self.stream_status_var.set(self._stream_status_line(snapshot, finished=finished))
        self._sync_live_stream_indicator(snapshot, finished=finished)
        if self.current_page == "chat":
            # During startup/page switches the chat Text widget can be absent or
            # already destroyed. Incremental render is used while streaming, but
            # stream finalization performs a full page rebuild from the supplied
            # final snapshot so the last assistant message cannot disappear.
            if finished:
                self._clear_content()
                page_root = self._prepare_page_root("chat")
                self._build_chat_page(page_root, snapshot)
                self._render_statusbar(snapshot)
                self._force_chat_scroll_to_end()
            else:
                if not self._render_live_chat_transcript(snapshot):
                    self._clear_content()
                    page_root = self._prepare_page_root("chat")
                    self._build_chat_page(page_root, snapshot)
                self._render_statusbar(snapshot)
            try:
                self.update_idletasks()
            except tk.TclError as exc:
                self._record_ui_warning("last_stream_update_error", exc, 120)
        else:
            self._render_statusbar(snapshot)
        if finished:
            self._mark_stream_worker_done()
            try:
                if self.current_page == "chat" and hasattr(self, "input_text"):
                    self.input_text.focus_set()
            except tk.TclError as exc:
                self._record_ui_warning("stream_final_focus", exc, 120)
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
            current_stage="前端流式线程失败；可点击重连继续监听或复制诊断。",
            stream_status="error",
            run_workbench_state="recoverable",
            run_status_label="可恢复",
            run_last_event="frontend_stream_error",
            run_reconnect_available=True,
            run_resume_available=True,
            run_stop_available=False,
            run_diagnostic_summary=f"frontend_stream_error: {safe_text(exc, 160)}",
        )
        self.stream_status_var.set("流式状态：error")
        self._finish_live_stream_indicator("已停止")
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
        self.stream_status_var.set(f"任务：已选中 任务会话摘要指纹={self.selected_session_id}")

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
            state = safe_text(getattr(self.snapshot, 'session_manager_state', 'requested'), 80)
            message = safe_text(getattr(self.snapshot, 'session_last_message', '') or getattr(self.snapshot, 'current_stage', ''), 180)
            self.stream_status_var.set(f"任务恢复请求：{state} · {message or session_id_digest}")
            self._show_frontend_notice("任务恢复请求已提交", f"任务会话={safe_text(session_id_digest, 60)}\n状态={state}\n{message or '恢复只提交运行时信封，本地前端不直接恢复工具。'}")
            self.show_page("sessions")
            return
        self._show_frontend_notice("恢复不可用", "当前 运行时客户端 不支持 Session 恢复请求；前端不会自行恢复工具或回滚。")

    def _show_session_detail(self, session_id_digest: str = "") -> None:
        sid = safe_text(session_id_digest or self.selected_session_id, 80)
        lines = [
            "L6.67 多任务 Session 管理器：",
            f"契约：{safe_text(getattr(self.snapshot, 'session_manager_contract', ''), 100)}",
            f"状态：{safe_text(getattr(self.snapshot, 'session_manager_state', ''), 80)}",
            f"最近消息：{safe_text(getattr(self.snapshot, 'session_last_message', ''), 220)}",
            "",
            "规则：",
            "- 前端只显示 Session 投影和提交 resume/search envelope。",
            "- 前端不得直接恢复工具、切换 运行时、写长期记忆、写审计或应用回滚。",
            "- 失败恢复、等待确认、任务归档必须继续由 运行时 / 天工网关 裁决。",
            "",
            "匹配任务：",
        ]
        found = False
        for item in list(getattr(self.snapshot, "task_sessions", []) or []):
            if not sid or safe_text(getattr(item, "session_id_digest", ""), 80) == sid:
                found = True
                lines.append(f"- {safe_text(getattr(item, 'title', ''), 120)} · {safe_text(getattr(item, 'status', ''), 40)} · 进度={getattr(item, 'progress_percent', 0)}% · 审计={safe_text(getattr(item, 'audit_id', ''), 80)} · 摘要指纹={safe_text(getattr(item, 'session_id_digest', ''), 80)}")
        if not found:
            lines.append("- 未找到匹配 Session。")
        self._show_safe_detail("任务详情", lines)

    def _show_installer_detail(self) -> None:
        s = self.snapshot
        manifest = getattr(s, "installer_manifest", None)
        lines = [
            "L6.69 安装器 / Windows 打包器 RC 前置结构：",
            f"契约：{safe_text(getattr(s, 'installer_rc_contract', ''), 100)}",
            f"stage：{safe_text(getattr(s, 'installer_stage', ''), 80)}",
            f"版本：{safe_text(getattr(manifest, 'version_label', ''), 100)}",
            f"开发者：{safe_text(getattr(manifest, 'unique_developer', ''), 80)}",
            f"天使投资人：{safe_text(getattr(manifest, 'angel_investor', ''), 80)}",
            f"update_channel：{safe_text(getattr(s, 'update_channel', ''), 80)}",
            f"startup_self_check_状态：{safe_text(getattr(s, 'startup_self_check_state', ''), 80)}",
            f"回滚就绪：{getattr(manifest, 'rollback_ready', False)}",
            f"离线修复可用：{getattr(manifest, 'offline_repair_available', False)}",
            "",
            "版本槽：",
        ]
        for slot in list(getattr(s, "version_slots", []) or [])[:12]:
            lines.append(f"- {safe_text(getattr(slot, 'slot_name', ''), 60)} · {safe_text(getattr(slot, 'state', ''), 40)} · {safe_text(getattr(slot, 'version_label', ''), 80)} · 摘要指纹={safe_text(getattr(slot, 'path_digest', ''), 80)}")
        lines.append("")
        lines.append("启动自检：")
        for check in list(getattr(s, "startup_self_checks", []) or [])[:20]:
            lines.append(f"- {safe_text(getattr(check, 'check_id', ''), 60)} · {safe_text(getattr(check, 'status', ''), 40)} · {safe_text(getattr(check, 'message', ''), 180)}")
        lines.append("")
        lines.append("边界：这是安装器/打包器/更新器/回滚器的前置结构展示。前端不可生成安装包、不可应用更新、不可恢复回滚槽、不可上传崩溃报告、不可修改 运行时 核心文件；L6.69 只允许 干运行 报告。")
        self._show_safe_detail("安装器 RC 详情", lines)

    def _run_startup_self_check(self) -> None:
        runner = getattr(self.client, "run_startup_self_check", None)
        if not callable(runner):
            self.installer_status_var.set("启动自检：当前 运行时客户端 不支持自检端点")
            self._show_frontend_notice("自检不可用", "当前 运行时客户端 不支持 /installer/startup/self-check；前端不会自行运行安装器脚本。")
            return
        self.snapshot = runner()
        self.installer_status_var.set(f"启动自检：{safe_text(getattr(self.snapshot, 'startup_self_check_state', 'updated'), 80)}")
        self.show_page("installer")

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
            self._show_frontend_notice("文件传输不可用", "当前 运行时客户端 不支持文件传输请求；前端不会自行读取并传输文件。")
            return
        self.snapshot = requester(path, "user_attachment")
        self.stream_status_var.set(f"文件传输：{safe_text(getattr(self.snapshot, 'file_transfer_state', 'requested'), 80)}")
        if bool(self.file_auto_run_var.get()):
            self._auto_submit_file_processing_task()
        else:
            self.show_page("files")

    def _auto_submit_file_processing_task(self) -> None:
        records = list(getattr(self.snapshot, "file_transfer_records", []) or [])
        rec = records[-1] if records else None
        file_name = safe_text(getattr(rec, "file_name", "附件"), 120) if rec else "附件"
        status = safe_text(getattr(rec, "status", "requested"), 80) if rec else "requested"
        if status in {"frontend_error", "blocked_by_hook"}:
            self.show_page("files")
            return
        prompt = (
            f"用户已上传附件：{file_name}。请进入 运行时文件处理链，读取/分析该附件并继续当前任务；"
            "如果缺少读取授权，请生成文件授权或确认请求。前端不直接读取文件正文、不直接执行工具。"
        )
        started = self._submit_text_to_runtime_stream(prompt, status=f"文件处理：已自动提交 运行时文件处理任务 · {file_name}")
        if started:
            self.show_page("chat")
        else:
            self.show_page("files")

    def _request_task_interrupt(self) -> None:
        self._release_stream_guard("interrupt")
        requester = getattr(self.client, "request_task_interrupt", None)
        if callable(requester):
            self.snapshot = requester("user_clicked_interrupt_button")
            self.stream_status_var.set(f"控制状态：{safe_text(getattr(self.snapshot, 'control_state', 'interrupt_requested'), 60)}")
            self.show_page(self.current_page)
            return
        self._show_frontend_notice("中断不可用", "当前 运行时客户端不支持中断请求；前端不会自行杀运行时 或工具。")

    def _request_file_authorization_from_dialog(self, mode: str = "read") -> None:
        mode_norm = safe_text(mode, 32).lower() or "read"
        try:
            if mode_norm in {"write", "read_write"}:
                path = filedialog.askdirectory(title="选择允许 运行时写入的输出目录")
                scope = "workspace_outbox"
                purpose = "workspace_output_write_directory"
            else:
                path = filedialog.askopenfilename(title="选择允许 运行时读取的本地文件")
                scope = "user_selected_file"
                purpose = "user_selected_workspace_authorization"
        except tk.TclError as exc:
            self._show_frontend_notice("文件授权不可用", f"当前环境无法打开文件选择器：{safe_text(exc, 160)}")
            return
        if not path:
            return
        requester = getattr(self.client, "request_file_authorization", None)
        if not callable(requester):
            self._show_frontend_notice("文件授权不可用", "当前 运行时客户端 不支持工作区文件授权请求；前端不会自行创建工作区或复制文件。")
            return
        self.snapshot = requester(path, mode_norm, scope, purpose)
        self.stream_status_var.set(f"工作区授权：{safe_text(getattr(self.snapshot, 'workspace_state', 'requested'), 80)} · {mode_norm}")
        self.show_page("workspace")

    def _show_workspace_detail(self) -> None:
        s = self.snapshot
        lines = [
            "L6.65 工作区 / 沙箱与文件授权边界：",
            f"契约：{safe_text(getattr(s, 'workspace_contract', ''), 100)}",
            f"状态：{safe_text(getattr(s, 'workspace_state', ''), 80)}",
            f"最近消息：{safe_text(getattr(s, 'workspace_last_message', ''), 220)}",
            "",
            "规则：",
            "- 前端只显示工作区策略和提交授权 envelope。",
            "- 前端不得创建工作区、修改 ACL、复制文件字节、显示原始路径或下载 token。",
            "- 写入授权必须继续经 运行时 / 质量门 / 天工网关 裁决。",
            "- 下载只显示中转回执与 token digest，不显示原始 token。",
            "",
            "最近授权：",
        ]
        for rec in list(getattr(s, "file_authorization_records", []) or [])[-20:]:
            lines.append(f"- {getattr(rec, 'file_name', '')} · {getattr(rec, 'mode', '')} · {getattr(rec, 'status', '')} · 路径摘要指纹={getattr(rec, 'path_digest', '')} · 审计={getattr(rec, 'audit_id', '')}")
        self._show_safe_detail("工作区详情", lines)

    def _show_file_transfer_detail(self) -> None:
        s = self.snapshot
        lines = [
            "L6.64/L6.65 文件传输与工作区边界：",
            f"契约：{safe_text(getattr(s, 'file_transfer_contract', ''), 100)}",
            f"状态：{safe_text(getattr(s, 'file_transfer_state', ''), 80)}",
            f"最近消息：{safe_text(getattr(s, 'file_transfer_last_message', ''), 220)}",
            "",
            "规则：",
            "- 前端只选择文件并生成脱敏 transfer request。",
            "- 报告与日志只保留文件名、大小、摘要和 运行时回执。",
            "- 原始路径、文件正文、模型服务凭证、审计写入和工具调用均禁止出现在前端层。",
            "- 真实读取、落盘、转存、下载中转必须由 运行时 / 天工网关 / 质量门 管控。",
            "",
            "最近记录：",
        ]
        for rec in list(getattr(s, "file_transfer_records", []) or [])[-20:]:
            lines.append(f"- {getattr(rec, 'file_name', '')} · {getattr(rec, 'status', '')} · 摘要指纹={getattr(rec, 'sha256_digest', '')} · 审计={getattr(rec, 'audit_id', '')}")
        self._show_safe_detail("文件传输详情", lines)

    def _request_connector_registration(self) -> None:
        name = safe_text(getattr(self, "connector_name_var", tk.StringVar(value="未命名连接器")).get(), 120)
        kind = connector_kind_value(getattr(self, "connector_kind_var", tk.StringVar(value="MCP 服务")).get())
        requester = getattr(self.client, "request_connector_registration", None)
        if not callable(requester):
            self.connector_status_var.set("连接器注册：当前 运行时客户端 不支持注册请求")
            self._show_frontend_notice("连接器注册不可用", "当前 运行时客户端 不支持连接器注册请求；前端不会自行安装 MCP 或执行连接器。")
            return
        self.connector_status_var.set("连接器注册：提交中")
        self.snapshot = requester(name, kind, ["read_public_metadata"], ["registry_review"])
        state = safe_text(getattr(self.snapshot, 'connector_registry_state', 'requested'), 80)
        message = safe_text(getattr(self.snapshot, 'connector_last_message', ''), 180)
        self.connector_status_var.set(f"连接器注册：{state} · {message or name}")
        self.stream_status_var.set(f"连接器注册：{state} · 已生成注册回执")
        # Keep a visible acknowledgement; previous builds changed the backing
        # snapshot but users could not tell whether the click had any effect.
        self._show_frontend_notice("连接器注册已提交", f"{name} · {kind} · {state}。默认禁用，只读待审；前端未安装或执行 MCP。")
        self.show_page("connectors")

    def _show_connector_detail(self) -> None:
        s = self.snapshot
        lines = [
            "L6.66 MCP / 连接器注册表前置治理：",
            f"契约：{safe_text(getattr(s, 'connector_registry_contract', ''), 100)}",
            f"状态：{safe_text(getattr(s, 'connector_registry_state', ''), 80)}",
            f"最近消息：{safe_text(getattr(s, 'connector_last_message', ''), 220)}",
            "",
            "规则：",
            "- 前端只显示注册表投影和提交注册 envelope。",
            "- 前端不得安装 MCP server、执行连接器、存储连接器密钥、直连外部 endpoint。",
            "- 连接器默认 禁用/只读；启用、隔离、执行必须经 运行时 / 质量门 / 工作区。",
            "- 开放市场一键安装在 RC 前置包中禁用。",
            "",
            "最近注册：",
        ]
        for rec in list(getattr(s, "connector_registration_records", []) or [])[-20:]:
            lines.append(f"- {getattr(rec, 'display_name', '')} · {getattr(rec, 'kind', '')} · {getattr(rec, 'status', '')} · 清单摘要指纹={getattr(rec, 'manifest_digest', '')} · 审计={getattr(rec, 'audit_id', '')}")
        self._show_safe_detail("连接器详情", lines)

    def _request_task_stop(self) -> None:
        self._release_stream_guard("stop")
        requester = getattr(self.client, "request_task_stop", None)
        if callable(requester):
            self.snapshot = requester("user_clicked_stop_button")
            self.stream_status_var.set(f"控制状态：{safe_text(getattr(self.snapshot, 'control_state', 'stop_requested'), 60)}")
            self.show_page(self.current_page)
            return
        self._show_frontend_notice("停止不可用", "当前 运行时客户端 不支持停止请求；前端不会自行停止工具。")

    def _request_task_reset(self) -> None:
        self._release_stream_guard("reset")
        requester = getattr(self.client, "request_task_reset", None)
        if callable(requester):
            self.snapshot = requester("user_clicked_reset_button")
            self.stream_status_var.set(f"控制状态：{safe_text(getattr(self.snapshot, 'control_state', 'reset_requested'), 60)}")
            self.show_page(self.current_page)
            return
        self._show_frontend_notice("复位不可用", "当前 运行时客户端不支持复位请求；前端不会自行复位运行时。")

    def _request_runtime_reconnect(self) -> None:
        getter = getattr(self.client, "get_run_status", None)
        if callable(getter):
            try:
                self.snapshot = getter()
                self.stream_status_var.set("任务工作台：已重新读取 /runs/status，继续监听当前 Run 状态")
                self.show_page(self.current_page)
                return
            except Exception as exc:
                self._record_ui_warning("run_status_reconnect", exc, 120)
        self._refresh_snapshot_frontend_only()
        self.stream_status_var.set("流式状态：已发起 运行时健康检查 重连刷新")

    def _submit_action_guard_decision(self, ticket_id: str, decision: str) -> None:
        if not ticket_id:
            self._show_frontend_notice("确认请求缺少票据", "缺少 ticket_id，前端不会构造本地放行。")
            return
        submit = getattr(self.client, "submit_confirmation", None)
        if callable(submit):
            self.snapshot = submit(ticket_id, decision)
        else:
            self.snapshot.submit_confirmation(ticket_id, decision)
        self.stream_status_var.set(f"确认请求：{safe_text(ticket_id, 60)} · {safe_text(decision, 32)} · {safe_text(getattr(self.snapshot, 'confirmation_request_state', 'submitted'), 80)}")
        self.show_page("execution")

    def _new_task_frontend_only(self) -> None:
        self._history_readonly_mode = False
        self._release_stream_guard("new_session")
        clearer = getattr(self.client, "clear_local_transcript", None)
        if callable(clearer):
            try:
                self.snapshot = clearer()
            except Exception as exc:
                self._record_ui_warning("new_session_clear_transcript", exc, 120)
        else:
            try:
                self.snapshot.chat_messages = []
                self.snapshot.visible_message_count = 0
                self.snapshot.hidden_message_count = 0
            except Exception as exc:
                self._record_ui_warning("new_session_snapshot_clear", exc, 120)
        self.show_page("chat")
        if hasattr(self, "input_text"):
            try:
                self.input_text.delete("1.0", "end")
                self.input_text.focus_set()
                self._sync_input_placeholder()
            except tk.TclError as exc:
                self._record_ui_warning("last_new_task_focus_error", exc, 120)
        self.stream_status_var.set("新会话：已清空前端会话并解除本地输入锁。")

    def _import_plan_frontend_only(self) -> None:
        try:
            path = filedialog.askopenfilename(title="选择要导入的计划文件")
        except tk.TclError as exc:
            self._show_frontend_notice("计划导入不可用", f"当前环境无法打开文件选择器：{safe_text(exc, 160)}")
            return
        if not path:
            self.stream_status_var.set("计划导入：已取消，未提交 运行时")
            return
        requester = getattr(self.client, "request_file_transfer", None)
        if not callable(requester):
            self._show_frontend_notice("计划导入不可用", "当前 运行时客户端 不支持文件传输请求；前端不会自行读取计划文件。")
            return
        self.snapshot = requester(path, "plan_import")
        self.stream_status_var.set("计划导入：已提交脱敏文件传输请求，未直接读取计划正文")
        self.show_page("files")
