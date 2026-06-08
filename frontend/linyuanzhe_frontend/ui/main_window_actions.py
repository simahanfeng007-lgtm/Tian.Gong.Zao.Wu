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
            self.stream_status_var.set("刷新完成：已读取 RuntimeClient 脱敏快照")
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
                    refresh = getattr(self.client, "refresh_snapshot", None)
                    self.snapshot = refresh() if callable(refresh) else self.client.get_snapshot()
                except Exception as exc:
                    self._record_ui_warning("last_snapshot_after_provider_save_error", exc, 120)
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
        # Raw Key/Base URL remain write-only from the frontend perspective.
        # Runtime may persist them; the UI only keeps configured/digest status.
        self.api_key_var.set("")
        self.api_base_url_var.set("")
        self._flash_settings_save_feedback("✓ 已保存；明文输入已清空")

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
        """Read the public Provider projection without calling the Provider SDK."""
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
            f"配置检查：{safe_text(readiness.get('label', '未知'), 40)}；state={state}；mode={mode}；"
            f"api_key_configured={key_ok}；key_digest={key_digest}；"
            f"base_url_configured={base_ok}；base_url_digest={base_digest}；"
            f"last_check={last_check}；last_error={last_error}；"
            f"next={last_next}。"
            "此检查只读 /settings/provider，不裸调 Provider；真实联调由会话发送链路触发。"
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
        if hasattr(self, "input_text"):
            text = self.input_text.get("1.0", "end-1c").strip()
        else:
            text = getattr(self, "input_var", tk.StringVar()).get().strip()
        if not text:
            self._show_frontend_notice("输入为空", "请输入消息；空输入不会提交到 Runtime。")
            return
        if hasattr(self, "input_text"):
            self.input_text.delete("1.0", "end")
            self._sync_input_placeholder()
        self._submit_text_to_runtime_stream(text, status="流式状态：提交中")

    def _clear_chat_view_frontend_only(self) -> None:
        body = getattr(self, "_chat_body_widget", None)
        if body is None:
            self.stream_status_var.set("前端清屏：聊天区未挂载；未提交 Runtime。")
            return
        try:
            if body.winfo_exists():
                body.configure(state="normal")
                body.delete("1.0", "end")
                self._chat_render_signatures = []
                self.stream_status_var.set("前端清屏完成：仅清除本地渲染，不删除 Runtime 会话。")
        except tk.TclError as exc:
            self._record_ui_warning("chat_clear_frontend_only", exc, 120)

    def _submit_text_to_runtime_stream(self, text: str, *, status: str = "流式状态：提交中") -> bool:
        text = safe_text(text, 4000).strip()
        if not text:
            return False
        with self._stream_lock:
            if self._stream_worker is not None and self._stream_worker.is_alive():
                self._show_frontend_notice("任务进行中", "当前已有流式任务在进行；请先等待收口，或向 Runtime 发送停止请求。")
                return False
        self.stream_status_var.set(status)
        self._start_live_stream_indicator("临渊者正在思考")
        submit_stream = getattr(self.client, "submit_user_message_streaming", None)
        if not callable(submit_stream):
            self.snapshot = self.client.submit_user_message(text)
            if self.current_page == "chat":
                if not self._render_live_chat_transcript(self.snapshot):
                    self.show_page("chat")
                self._render_statusbar(self.snapshot)
                self.stream_status_var.set("流式状态：completed")
                self._finish_live_stream_indicator("已完成")
            else:
                self.show_page("chat")
            return True

        def on_snapshot(snapshot: RuntimeSnapshot) -> None:
            self._post_to_ui(lambda snap=snapshot: self._queue_stream_snapshot(snap))

        def worker() -> None:
            try:
                snapshot = submit_stream(text, on_snapshot=on_snapshot)
                self._post_to_ui(lambda snap=snapshot: self._queue_stream_snapshot(snap, finished=True, force=True))
            except Exception as exc:
                self._post_to_ui(lambda err=exc: self._stream_failed(err))

        t = threading.Thread(target=worker, name="linyuanzhe-runtime-sse-stream", daemon=True)
        with self._stream_lock:
            self._stream_worker = t
        t.start()
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
            # Keep the transcript pinned to the newest delta immediately. Rebuild
            # the full page only when the chat Text widget no longer exists.
            if not self._render_live_chat_transcript(snapshot):
                self.show_page("chat")
            self._render_statusbar(snapshot)
            try:
                self.update_idletasks()
            except tk.TclError as exc:
                self._record_ui_warning("last_stream_update_error", exc, 120)
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
        self.stream_status_var.set(f"任务：已选中 session_digest={self.selected_session_id}")

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
        self._show_safe_detail("任务详情", lines)

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

    def _run_startup_self_check(self) -> None:
        runner = getattr(self.client, "run_startup_self_check", None)
        if not callable(runner):
            self.installer_status_var.set("启动自检：当前 RuntimeClient 不支持自检端点")
            self._show_frontend_notice("自检不可用", "当前 RuntimeClient 不支持 /installer/startup/self-check；前端不会自行运行安装器脚本。")
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
            self._show_frontend_notice("文件传输不可用", "当前 RuntimeClient 不支持文件传输请求；前端不会自行读取并传输文件。")
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
            f"用户已上传附件：{file_name}。请进入 Runtime 文件处理链，读取/分析该附件并继续当前任务；"
            "如果缺少读取授权，请生成文件授权或确认请求。前端不直接读取文件正文、不直接执行工具。"
        )
        started = self._submit_text_to_runtime_stream(prompt, status=f"文件处理：已自动提交 Runtime 文件处理任务 · {file_name}")
        if started:
            self.show_page("chat")
        else:
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
        mode_norm = safe_text(mode, 32).lower() or "read"
        try:
            if mode_norm in {"write", "read_write"}:
                path = filedialog.askdirectory(title="选择允许 Runtime 写入的输出目录")
                scope = "workspace_outbox"
                purpose = "workspace_output_write_directory"
            else:
                path = filedialog.askopenfilename(title="选择允许 Runtime 读取的本地文件")
                scope = "user_selected_file"
                purpose = "user_selected_workspace_authorization"
        except tk.TclError as exc:
            self._show_frontend_notice("文件授权不可用", f"当前环境无法打开文件选择器：{safe_text(exc, 160)}")
            return
        if not path:
            return
        requester = getattr(self.client, "request_file_authorization", None)
        if not callable(requester):
            self._show_frontend_notice("文件授权不可用", "当前 RuntimeClient 不支持工作区文件授权请求；前端不会自行创建工作区或复制文件。")
            return
        self.snapshot = requester(path, mode_norm, scope, purpose)
        self.stream_status_var.set(f"工作区授权：{safe_text(getattr(self.snapshot, 'workspace_state', 'requested'), 80)} · {mode_norm}")
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
            self.connector_status_var.set("连接器注册：当前 RuntimeClient 不支持注册请求")
            self._show_frontend_notice("连接器注册不可用", "当前 RuntimeClient 不支持连接器注册请求；前端不会自行安装 MCP 或执行连接器。")
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
        submit = getattr(self.client, "submit_confirmation", None)
        if callable(submit):
            self.snapshot = submit(ticket_id, decision)
        else:
            self.snapshot.submit_confirmation(ticket_id, decision)
        self.stream_status_var.set(f"确认请求：{safe_text(ticket_id, 60)} · {safe_text(decision, 32)} · {safe_text(getattr(self.snapshot, 'confirmation_request_state', 'submitted'), 80)}")
        self.show_page("execution")

    def _new_task_frontend_only(self) -> None:
        self.show_page("chat")
        if hasattr(self, "input_text"):
            try:
                self.input_text.delete("1.0", "end")
                self.input_text.focus_set()
            except tk.TclError as exc:
                self._record_ui_warning("last_new_task_focus_error", exc, 120)
        self.stream_status_var.set("新建任务：已打开输入栏，尚未提交 Runtime")

    def _import_plan_frontend_only(self) -> None:
        try:
            path = filedialog.askopenfilename(title="选择要导入的计划文件")
        except tk.TclError as exc:
            self._show_frontend_notice("计划导入不可用", f"当前环境无法打开文件选择器：{safe_text(exc, 160)}")
            return
        if not path:
            self.stream_status_var.set("计划导入：已取消，未提交 Runtime")
            return
        requester = getattr(self.client, "request_file_transfer", None)
        if not callable(requester):
            self._show_frontend_notice("计划导入不可用", "当前 RuntimeClient 不支持文件传输请求；前端不会自行读取计划文件。")
            return
        self.snapshot = requester(path, "plan_import")
        self.stream_status_var.set("计划导入：已提交脱敏文件传输请求，未直接读取计划正文")
        self.show_page("files")
