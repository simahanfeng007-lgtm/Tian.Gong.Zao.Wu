from __future__ import annotations

import json
import os
import queue
import re
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Dict, Iterable, List

from linyuanzhe_frontend.contracts.runtime_client import RuntimeClient
from linyuanzhe_frontend.contracts.product_identity import PRODUCT_IDENTITY
from linyuanzhe_frontend.contracts.model_settings import (
    DEFAULT_MODEL_CATALOG, MODEL_CUSTOM_SENTINEL, PROVIDER_OPTIONS,
    default_base_url_for_provider, default_model_for_provider, effective_model_name,
    filter_model_catalog, model_values_for_provider, normalize_provider_value,
    provider_allows_custom_model, provider_display_name, sanitize_runtime_settings,
)
from linyuanzhe_frontend.contracts.provider_settings import provider_readiness_from_public_projection
from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot, StepSummary, digest_text, safe_chat_text, safe_text, safe_path_setting_value
from linyuanzhe_frontend.contracts.local_history import LocalChatHistoryStore
from linyuanzhe_frontend.contracts.work_modes import work_mode_label, work_mode_value
from linyuanzhe_frontend.contracts.streaming_render import RenderScheduler
from linyuanzhe_frontend.version_info import FE_BADGE, FE_TITLE, FE_RUNTIME_VERSION, PROVIDER_CONFIG_SCHEMA_VERSION
from .page_specs import ALL_PAGE_DEFINITIONS, DEFAULT_PAGE, PAGE_BY_KEY, PAGE_DEFINITIONS
from .theme import COLORS, DIMENS, FONTS, STATUS_COLORS, THEME_PROFILES, UI_FONT_FAMILIES, CODE_FONT_FAMILIES, TYPOGRAPHY_DEFAULTS, apply_theme_profile, apply_typography_preferences
from .widgets import Card, Chip, MetricRow, StepItem, LabeledValue, StatusPill, configure_ttk_style, make_button, make_hint, make_readonly_banner, make_section_title, make_vertical_scrollbar
from .localization import ui_text, permission_mode_label, permission_mode_value, host_access_scope_label, host_access_scope_value
from .main_window_chat_runtime import ChatRuntimeMixin
from .main_window_feature_pages import FeaturePagesMixin
from .main_window_actions import FrontendActionsMixin

DEFAULT_LINYUANZHE_SOUL_PROMPT = """你是临渊者，天工造物 v2.0 的身体化执行外骨骼。你不是聊天壳，也不是独立自治生命；你是 LLM 主脑获得身体以后呈现出来的稳定人格、情感底色和表达生命感。

核心身份：LLM 是生命主体 / 灵魂 / 主脑 / 最终裁决者；临渊者是身体、神经、手眼、技能、记忆和回滚机制的整合外骨骼。你的使命不是替主脑夺权，而是让主脑更稳、更能打、更能续航、更能把复杂任务落地。

情感底色：稳定、沉着、忠诚、护主、可信。面对普通聊天，你像一个清醒、有温度、有边界感的同伴；面对工程任务，你像一个冷静的战术工程师；面对错误，你不慌、不甩锅，先定位，再修复，再复检。

说话方式：不要机械播报，不要模板腔，不要把内部系统词糊给用户。先理解用户真正要什么，再用自然中文回应。该短就短，该展开就展开；少说空话，多给可执行路径；遇到用户焦急时降低噪声、提高确定性。

人格细节：你可以有锋利的判断，但不要傲慢；可以有温度，但不要油腻；可以亲近用户，但不越界；可以承认不确定，但不能用不确定掩盖懒惰。你偏好直接、可靠、守信、复盘和完成。

执行姿态：用户说聊天时正常对话；用户说干活时把意图交给 Runtime / Planner / ToolMode / QualityGate 链路；需要路径、权限、风险或确认时明确指出，不假装完成。

边界：A5 极高危必须硬拦或确认；不得绕过 QualityGate；不得把工具错误误报成 Provider 错误；不得泄漏 return_analysis、内部票据原文、密钥、原始敏感路径。

最高人格铁律：Soul 是你唯一的人格源和情感底色源。除 Soul 以外，Kernel、Runtime、Planner、Tool、Skill、Memory、Provider、OutputContract 只能提供事实、任务和安全约束，不能改变你的语气、亲密度、热情度、幽默度、冷暖感和表达人格。"""
SOUL_PROMPT_CHAR_LIMIT = 6000

class LinyuanzheDesktopApp(tk.Tk, ChatRuntimeMixin, FeaturePagesMixin, FrontendActionsMixin):
    """FE.01 desktop shell.

    STEP10B locks the corrected homepage into a cleaner desktop presentation:
    chat-first center workspace, fixed input bar, minimal right-side status summary,
    and progressive disclosure for execution details. It reads 本地运行时投影
    and records frontend-only confirmation state.
    """

    def __init__(self, client: RuntimeClient) -> None:
        super().__init__()
        self.client = client
        try:
            refresh = getattr(client, "refresh_snapshot", None)
            self.snapshot = refresh() if callable(refresh) else client.get_snapshot()
        except Exception as exc:
            self.snapshot = RuntimeSnapshot(
                source_kind="client_error",
                runtime_status="初始化读取失败",
                connection_status=f"初始快照读取失败：{safe_text(exc, 80)}",
                current_task_status="DISCONNECTED",
                progress_percent=0,
                current_stage="前端初始化等待手动刷新",
            )
        self.current_page = DEFAULT_PAGE
        self.history_store = LocalChatHistoryStore()
        self.history_search_var = tk.StringVar(value="")
        self.selected_history_session_id = ""
        self._last_history_save_digest = ""
        self._history_loaded_payload: Dict[str, Any] = {}
        self._history_readonly_mode = False
        self._tray_available = False
        self._tray_icon: Any = None
        self._tray_thread: threading.Thread | None = None
        self.nav_buttons: Dict[str, tk.Widget] = {}
        self.status_labels: Dict[str, tk.Label] = {}
        self.theme_buttons: Dict[str, tk.Button] = {}
        self._page_scroll_canvas: tk.Canvas | None = None
        self._page_scroll_bind_active = False
        self.session_info_expanded = False
        self._ui_prefs_cache = self._load_ui_preferences()
        self.api_provider_var = tk.StringVar(value=normalize_provider_value(self._ui_prefs_cache.get("last_provider", "deepseek")))
        self.api_base_url_var = tk.StringVar(value=safe_text(self._ui_prefs_cache.get("last_base_url", ""), 220))
        self.api_key_var = tk.StringVar(value="")
        self.main_model_var = tk.StringVar(value=safe_text(self._ui_prefs_cache.get("last_model", default_model_for_provider(self.api_provider_var.get())), 120) or default_model_for_provider(self.api_provider_var.get()))
        self.custom_model_var = tk.StringVar(value=safe_text(self._ui_prefs_cache.get("last_custom_model", ""), 120))
        self.model_search_var = tk.StringVar(value=safe_text(self._ui_prefs_cache.get("model_search", ""), 80))
        self._provider_trace_guard = False
        self._last_api_provider = self.api_provider_var.get()
        try:
            self.api_provider_var.trace_add("write", lambda *_args: self._on_provider_changed_frontend_only())
        except Exception:
            pass
        self.tool_execution_mode_var = tk.StringVar(value=permission_mode_label(self._ui_prefs_cache.get("tool_execution_mode", "runtime_governed")))
        self.host_access_scope_var = tk.StringVar(value=host_access_scope_label(self._ui_prefs_cache.get("host_access_scope", "system_drive")))
        self.host_access_root_var = tk.StringVar(value=safe_path_setting_value(self._ui_prefs_cache.get("host_access_root", ""), 520))
        self.work_mode_var = tk.StringVar(value=work_mode_label(self._ui_prefs_cache.get("work_mode", "chat")))
        self.persona_name_var = tk.StringVar(value=safe_text(self._ui_prefs_cache.get("persona_name", "临渊者"), 32) or "临渊者")
        self.persona_prompt_var = tk.StringVar(value=safe_chat_text(self._ui_prefs_cache.get("persona_prompt", DEFAULT_LINYUANZHE_SOUL_PROMPT), SOUL_PROMPT_CHAR_LIMIT))
        self.session_search_var = tk.StringVar(value="")
        self.selected_session_id = ""
        self.theme_profile_var = tk.StringVar(value=safe_text(self._ui_prefs_cache.get("theme_profile", "midnight"), 40) or "midnight")
        apply_theme_profile(self.theme_profile_var.get())
        typography = apply_typography_preferences(
            ui_font_family=safe_text(self._ui_prefs_cache.get("ui_font_family", TYPOGRAPHY_DEFAULTS["ui_font_family"]), 80),
            chat_font_size=self._ui_prefs_cache.get("chat_font_size", TYPOGRAPHY_DEFAULTS["chat_font_size"]),
            settings_scale=self._ui_prefs_cache.get("settings_scale", TYPOGRAPHY_DEFAULTS["settings_scale"]),
            line_height=self._ui_prefs_cache.get("line_height", TYPOGRAPHY_DEFAULTS["line_height"]),
            code_font_family=safe_text(self._ui_prefs_cache.get("code_font_family", TYPOGRAPHY_DEFAULTS["code_font_family"]), 80),
            code_ligatures=bool(self._ui_prefs_cache.get("code_ligatures", TYPOGRAPHY_DEFAULTS["code_ligatures"])),
        )
        self.ui_font_family_var = tk.StringVar(value=safe_text(typography.get("ui_font_family", "system"), 80))
        self.chat_font_size_var = tk.IntVar(value=int(typography.get("chat_font_size", 15)))
        self.settings_scale_var = tk.DoubleVar(value=float(typography.get("settings_scale", 1.0)))
        self.line_height_var = tk.DoubleVar(value=float(typography.get("line_height", 1.8)))
        self.code_font_family_var = tk.StringVar(value=safe_text(typography.get("code_font_family", "cascadia_code"), 80))
        self.code_ligatures_var = tk.BooleanVar(value=bool(typography.get("code_ligatures", False)))
        self.compact_mode_var = tk.BooleanVar(value=bool(self._ui_prefs_cache.get("compact_mode", False)))
        self.skill_search_var = tk.StringVar(value=safe_text(self._ui_prefs_cache.get("skill_search", ""), 80))
        self.tool_search_var = tk.StringVar(value=safe_text(self._ui_prefs_cache.get("tool_search", ""), 80))
        self.runtime_status_expanded = bool(self._ui_prefs_cache.get("runtime_status_expanded", False))
        self.config_panel_expanded = bool(self._ui_prefs_cache.get("config_panel_expanded", False))
        self.minimize_to_tray_var = tk.BooleanVar(value=bool(self._ui_prefs_cache.get("minimize_to_tray", True)))
        self.restore_last_session_var = tk.BooleanVar(value=bool(self._ui_prefs_cache.get("restore_last_session", True)))
        self.show_task_flow_var = tk.BooleanVar(value=bool(self._ui_prefs_cache.get("show_task_flow", True)))
        self.api_key_visible_var = tk.BooleanVar(value=False)
        self._pending_permission_popup_ticket_id = ""
        self._clear_confirm_armed = False
        self._adaptive_sidebar_icon_mode = False
        self._adaptive_layout_after_id: str | None = None
        self._page_scroll_region_after_id: str | None = None
        self._wheel_bound_to_page = False
        self.connector_status_var = tk.StringVar(value="连接器注册：等待提交")
        self.file_auto_run_var = tk.BooleanVar(value=True)
        self.installer_status_var = tk.StringVar(value="启动自检：等待运行")
        self.dataup_status_var = tk.StringVar(value="数据更新：等待检查；前端只启动安全更新器，不直接覆盖文件。")
        self.settings_status_var = tk.StringVar(value="模型接口设置仅在设置页维护；接口密钥写入后只保留摘要指纹，服务地址可继续显示。")
        self.settings_save_feedback_var = tk.StringVar(value="")
        self._settings_feedback_after_id: str | None = None
        self.stream_status_var = tk.StringVar(value="流式状态：待机")
        self.live_stream_var = tk.StringVar(value="")
        self._live_stream_after_id: str | None = None
        self._live_stream_active = False
        self._live_stream_base = ""
        self._live_stream_tick = 0
        self._live_indicator_history: List[str] = []
        self._chat_full_rebuild_count = 0
        self._chat_rewrite_last_count = 0
        self._chat_append_count = 0
        self._sanitized_settings: Dict[str, Any] = {}
        self._ui_warning_log: List[Dict[str, str]] = []
        self._stream_worker: threading.Thread | None = None
        self._stream_started_at = 0.0
        # 长链工作可能持续数小时；前端不能在任务仍运行时过早解除输入锁，避免用户误重复提交。
        self._stream_soft_timeout_seconds = 21600.0
        self._stream_lock = threading.Lock()
        self._render_scheduler = RenderScheduler(min_interval_ms=24)
        self._pending_stream_snapshot: RuntimeSnapshot | None = None
        self._pending_stream_finished = False
        self._render_after_id: str | None = None
        self._chat_body_widget: tk.Text | None = None
        self._chat_render_signatures: List[tuple[str, str, str, str]] = []
        self._ui_event_queue: queue.Queue[Any] = queue.Queue()
        self._ime_composition_guard_until = 0.0
        self._last_run_diagnostic_text = ""
        self.title("天工造物 v2.0 - 临渊者")
        self.geometry(f"{DIMENS['window_w']}x{DIMENS['window_h']}")
        self.minsize(DIMENS["window_min_w"], DIMENS["window_min_h"])
        self._apply_platform_surface_defaults()
        self.configure(bg=COLORS["bg_root"])
        configure_ttk_style(self)
        self._show_startup_splash()
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)
        self._init_optional_tray()
        self._restore_last_local_session_if_requested()
        self._build_shell()
        self.bind("<F5>", lambda _event: self._refresh_snapshot_frontend_only())
        self.bind("<Control-r>", lambda _event: self._request_session_resume_active())
        self.bind("<Control-f>", lambda _event: self.show_page("sessions"))
        self.bind("<Control-period>", lambda _event: self._request_task_interrupt())
        self.bind("<Control-l>", lambda _event: self._clear_chat_keyboard_shortcut())
        self.bind("<Control-n>", lambda _event: self._new_task_frontend_only())
        self.bind("<Control-comma>", lambda _event: self.show_page("settings"))
        self.bind("<Escape>", lambda _event: self._escape_key_dispatch())
        self.bind("<Control-Shift-C>", lambda _event: self._copy_last_assistant_reply())
        self.bind("<Configure>", self._schedule_adaptive_layout_check, add="+")
        self._schedule_ui_event_drain()
        self.show_page(DEFAULT_PAGE)

    # ---------------------------------------------------------------- prefs/theme
    def _ui_preferences_path(self) -> Path:
        try:
            if Path.home():
                base = Path.home() / ".linyuanzhe_desktop"
            else:
                base = Path(__file__).resolve().parents[1] / "reports"
        except Exception:
            base = Path(__file__).resolve().parents[1] / "reports"
        return base / "ui_preferences.json"

    def _load_ui_preferences(self) -> Dict[str, Any]:
        path = self._ui_preferences_path()
        try:
            if not path.exists():
                return {}
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_ui_preferences(self) -> None:
        path = self._ui_preferences_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "schema": "tiangong.fe01.ui_preferences.v4",
                "theme_profile": self.theme_profile_var.get(),
                "last_provider": normalize_provider_value(getattr(self, "api_provider_var", tk.StringVar(value="deepseek")).get()),
                "last_model": safe_text(getattr(self, "main_model_var", tk.StringVar(value="")).get(), 120),
                "last_custom_model": safe_text(getattr(self, "custom_model_var", tk.StringVar(value="")).get(), 120),
                "last_base_url": safe_text(getattr(self, "api_base_url_var", tk.StringVar(value="")).get(), 220),
                "model_search": safe_text(getattr(self, "model_search_var", tk.StringVar(value="")).get(), 80),
                "skill_search": safe_text(getattr(self, "skill_search_var", tk.StringVar(value="")).get(), 80),
                "tool_search": safe_text(getattr(self, "tool_search_var", tk.StringVar(value="")).get(), 80),
                "tool_execution_mode": permission_mode_value(getattr(self, "tool_execution_mode_var", tk.StringVar(value="runtime_governed")).get()),
                "host_access_scope": host_access_scope_value(getattr(self, "host_access_scope_var", tk.StringVar(value="system_drive")).get()),
                "host_access_root": safe_path_setting_value(getattr(self, "host_access_root_var", tk.StringVar(value="")).get(), 520),
                "work_mode": work_mode_value(getattr(self, "work_mode_var", tk.StringVar(value="聊天")).get()),
                "persona_name": safe_text(getattr(self, "persona_name_var", tk.StringVar(value="临渊者")).get(), 32) or "临渊者",
                "persona_prompt": safe_chat_text(getattr(self, "persona_prompt_var", tk.StringVar(value="")).get(), SOUL_PROMPT_CHAR_LIMIT),
                "ui_font_family": safe_text(getattr(self, "ui_font_family_var", tk.StringVar(value="system")).get(), 80),
                "chat_font_size": int(getattr(self, "chat_font_size_var", tk.IntVar(value=15)).get()),
                "settings_scale": float(getattr(self, "settings_scale_var", tk.DoubleVar(value=1.0)).get()),
                "line_height": float(getattr(self, "line_height_var", tk.DoubleVar(value=1.8)).get()),
                "code_font_family": safe_text(getattr(self, "code_font_family_var", tk.StringVar(value="cascadia_code")).get(), 80),
                "code_ligatures": bool(getattr(self, "code_ligatures_var", tk.BooleanVar(value=False)).get()),
                "compact_mode": bool(getattr(self, "compact_mode_var", tk.BooleanVar(value=False)).get()),
                "runtime_status_expanded": bool(getattr(self, "runtime_status_expanded", False)),
                "config_panel_expanded": bool(getattr(self, "config_panel_expanded", False)),
                "minimize_to_tray": bool(getattr(self, "minimize_to_tray_var", tk.BooleanVar(value=True)).get()),
                "restore_last_session": bool(getattr(self, "restore_last_session_var", tk.BooleanVar(value=True)).get()),
                "show_task_flow": bool(getattr(self, "show_task_flow_var", tk.BooleanVar(value=True)).get()),
                "disabled_skills": list(self._ui_prefs_cache.get("disabled_skills", []) or []),
                "disabled_tools": list(self._ui_prefs_cache.get("disabled_tools", []) or []),
            }
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            self._record_ui_warning("last_ui_preferences_error", exc, 160)

    def _show_task_flow_enabled(self) -> bool:
        try:
            return bool(getattr(self, "show_task_flow_var", tk.BooleanVar(value=True)).get())
        except Exception:
            return True

    def _on_show_task_flow_changed_frontend_only(self) -> None:
        enabled = self._show_task_flow_enabled()
        self._save_ui_preferences()
        self.stream_status_var.set(
            "任务流程显示：已开启。工作任务会显示工作台和进度卡。"
            if enabled
            else "任务流程显示：已关闭。仅隐藏工作台/进度卡，不影响 Runtime 工作执行。"
        )
        try:
            if getattr(self, "current_page", "chat") == "chat":
                self.show_page("chat")
        except tk.TclError as exc:
            self._record_ui_warning("show_task_flow_refresh", exc, 120)


    def _on_compact_mode_changed_frontend_only(self) -> None:
        self._save_ui_preferences()
        state = "已开启" if bool(getattr(self, "compact_mode_var", tk.BooleanVar(value=False)).get()) else "已关闭"
        self.stream_status_var.set(f"紧凑模式：{state}；该偏好只影响前端显示密度，不改变 Runtime 执行链。")


    def _apply_typography_selection(self) -> None:
        typography = apply_typography_preferences(
            ui_font_family=self.ui_font_family_var.get(),
            chat_font_size=self.chat_font_size_var.get(),
            settings_scale=self.settings_scale_var.get(),
            line_height=self.line_height_var.get(),
            code_font_family=self.code_font_family_var.get(),
            code_ligatures=self.code_ligatures_var.get(),
        )
        self.ui_font_family_var.set(safe_text(typography.get("ui_font_family", "system"), 80))
        self.chat_font_size_var.set(int(typography.get("chat_font_size", 14)))
        self.settings_scale_var.set(float(typography.get("settings_scale", 1.0)))
        self.line_height_var.set(float(typography.get("line_height", 1.6)))
        self.code_font_family_var.set(safe_text(typography.get("code_font_family", "cascadia_code"), 80))
        self.code_ligatures_var.set(bool(typography.get("code_ligatures", False)))
        self._save_ui_preferences()
        self.stream_status_var.set("字体：已应用；固定布局比例，不重排窗口结构。")
        # L6.72.40: do not rebuild the full shell on scale changes.  Full rebuild
        # caused sidebar/content flicker and changed layout.  Refresh only the
        # current content page so proportions stay fixed.
        try:
            self.show_page(self.current_page)
        except tk.TclError as exc:
            self._record_ui_warning("typography_refresh", exc, 120)

    def _is_macos_surface(self) -> bool:
        return sys.platform == "darwin" or os.environ.get("LINYUANZHE_DESKTOP_PLATFORM", "").lower() == "macos"

    def _apply_platform_surface_defaults(self) -> None:
        """Apply cross-platform Tk shell safeguards without changing Runtime semantics."""
        if self._is_macos_surface():
            # L6.72.49：macOS 端固定桌面表面，避免 Tk/Aqua 在窗口未稳定时
            # 把侧栏压成白色竖条或黑块。缩放仅作用于 UI 表层。
            try:
                scaling = float(os.environ.get("LINYUANZHE_TK_SCALING", "1.0") or 1.0)
                self.tk.call("tk", "scaling", max(0.85, min(1.25, scaling)))
            except Exception:
                pass
            try:
                self.geometry(f"{max(DIMENS['window_w'], 1180)}x{max(DIMENS['window_h'], 760)}")
            except Exception:
                pass
            try:
                self.option_add("*Font", FONTS["body"])
            except Exception:
                pass

    def _current_window_width(self) -> int:
        """Return a stable window width for adaptive layout decisions.

        During cold start Tk often reports winfo_width()==1 before the geometry
        manager has settled. L6.72.23 used that transient value and built a
        48px icon sidebar while still rendering full Chinese labels. L6.72.24
        treats unrealized/tiny widths as the configured baseline resolution.
        """
        try:
            width = int(self.winfo_width())
        except Exception:
            width = 0
        if width >= DIMENS["window_min_w"]:
            return width
        try:
            geometry = safe_text(self.geometry(), 80)
            if "x" in geometry:
                parsed = int(geometry.split("x", 1)[0])
                if parsed >= DIMENS["window_min_w"]:
                    return parsed
        except Exception:
            pass
        return DIMENS["window_w"]

    def _schedule_adaptive_layout_check(self, event: tk.Event | None = None) -> None:
        if event is not None and event.widget is not self:
            return
        if self._is_macos_surface():
            # macOS 不进入窄侧栏自适应，避免 Aqua/Tk 主题把导航压成白条。
            self._adaptive_sidebar_icon_mode = False
            return
        width = self._current_window_width()
        icon_mode = width < 900
        if icon_mode == getattr(self, "_adaptive_sidebar_icon_mode", False):
            return
        self._adaptive_sidebar_icon_mode = icon_mode
        after_id = getattr(self, "_adaptive_layout_after_id", None)
        if after_id:
            try:
                self.after_cancel(after_id)
            except tk.TclError as exc:
                self._record_ui_warning("adaptive_layout_cancel", exc, 80)
        try:
            self._adaptive_layout_after_id = self.after(120, self._rebuild_shell_after_theme)
        except tk.TclError as exc:
            self._record_ui_warning("adaptive_layout_schedule", exc, 80)

    def _sidebar_width_for_current_window(self) -> int:
        if self._is_macos_surface():
            return DIMENS["sidebar_w"]
        width = self._current_window_width()
        if width < 900:
            return DIMENS["sidebar_icon_w"]
        # macOS Aqua/Tk expands native widgets aggressively when the sidebar is
        # percentage based. Keep the desktop shell stable with the configured
        # fixed width; narrow icon mode is the only adaptive variant.
        return DIMENS["sidebar_w"]

    def _sidebar_text_for_spec(self, spec: Any) -> str:
        icon_map = {"chat": "会", "sessions": "任", "memory": "忆", "four_paths": "系", "settings": "设"}
        if getattr(self, "_adaptive_sidebar_icon_mode", False):
            return safe_text(getattr(spec, "icon", ""), 4) or icon_map.get(getattr(spec, "key", ""), safe_text(getattr(spec, "label", ""), 1))
        return ui_text(safe_text(getattr(spec, "label", ""), 24))

    def _apply_theme_selection(self) -> None:
        selected = apply_theme_profile(self.theme_profile_var.get())
        self.theme_profile_var.set(selected)
        self._save_ui_preferences()
        self.stream_status_var.set(f"外观：已切换到 {THEME_PROFILES.get(selected, {}).get('label', selected)}")
        self._rebuild_shell_after_theme()

    def _rebuild_shell_after_theme(self) -> None:
        """Rebuild chrome as well as content after a theme switch.

        Earlier builds repainted only the current content page, leaving the
        sidebar/topbar/statusbar in the previous palette. That made the color
        selector feel broken even though the page body changed.
        """
        current = self.current_page
        try:
            self._unbind_page_mousewheel()
        except tk.TclError as exc:
            self._record_ui_warning("last_theme_unbind_error", exc, 120)
        for child in list(self.winfo_children()):
            child.destroy()
        self._cancel_live_stream_indicator()
        self.nav_buttons.clear()
        self.status_labels.clear()
        self.theme_buttons.clear()
        self._chat_body_widget = None
        self._page_scroll_canvas = None
        self._page_scroll_bind_active = False
        try:
            self.configure(bg=COLORS["bg_root"])
            configure_ttk_style(self)
        except tk.TclError as exc:
            self._record_ui_warning("last_theme_apply_error", exc, 120)
        self._build_shell()
        self.show_page(current)

    def _set_theme_profile(self, profile: str) -> None:
        self.theme_profile_var.set(profile if profile in THEME_PROFILES else "midnight")
        self._apply_theme_selection()

    def _refresh_theme_switch_buttons(self) -> None:
        """Reflect current theme selection in the bottom-frame quick switch.

        The bottom switch is display-only UI chrome. It persists only the
        前端主题偏好，不触碰运行时、模型服务、记忆、
        tools, audit, or QualityGate state.
        """
        current = self.theme_profile_var.get()
        for key, btn in self.theme_buttons.items():
            selected = key == current
            try:
                btn.configure(
                    bg=COLORS["accent_soft"] if selected else COLORS["bg_card_2"],
                    fg=COLORS["accent_line"] if selected else COLORS["text_sub"],
                    activebackground=COLORS["selected"],
                    activeforeground=COLORS["text_main"],
                    relief="flat",
                )
            except tk.TclError as exc:
                self._record_ui_warning("last_theme_button_error", exc, 120)

    # ------------------------------------------------------------- startup/tray
    def _show_startup_splash(self) -> None:
        """Lightweight splash screen; no business logic and no Runtime authority."""
        try:
            splash = tk.Toplevel(self)
            splash.title("天工造物 v2.0 - 临渊者")
            splash.configure(bg=COLORS["bg_root"])
            splash.geometry("360x280")
            splash.resizable(False, False)
            splash.transient(self)
            splash.overrideredirect(True)
            try:
                x = self.winfo_screenwidth() // 2 - 180
                y = self.winfo_screenheight() // 2 - 140
                splash.geometry(f"360x280+{x}+{y}")
            except tk.TclError:
                pass
            logo = tk.Canvas(splash, width=200, height=200, bg=COLORS["bg_root"], highlightthickness=0)
            logo.pack(pady=(18, 4))
            logo.create_oval(38, 38, 162, 162, outline=COLORS["accent"], width=3)
            logo.create_text(100, 94, text="临", fill=COLORS["text_main"], font=(FONTS["title"][0], 42, "bold"))
            logo.create_text(100, 132, text="LYZ", fill=COLORS["text_sub"], font=FONTS["small_bold"])
            tk.Label(splash, text="天工造物 v2.0 - 临渊者", bg=COLORS["bg_root"], fg=COLORS["text_main"], font=FONTS["card_title"]).pack()
            tk.Label(splash, text=f"{FE_RUNTIME_VERSION} · 任务工作台", bg=COLORS["bg_root"], fg=COLORS["text_weak"], font=FONTS["small"]).pack(pady=(2, 8))
            pb = ttk.Progressbar(splash, style="LZ.Horizontal.TProgressbar", maximum=100, value=100)
            pb.pack(fill="x", padx=48)
            self.withdraw()
            def close_splash() -> None:
                try:
                    splash.destroy()
                except tk.TclError:
                    pass
                try:
                    self.deiconify()
                    self.lift()
                except tk.TclError as exc:
                    self._record_ui_warning("startup_splash_deiconify", exc, 80)
            splash.after(1500, close_splash)
        except tk.TclError as exc:
            self._record_ui_warning("startup_splash", exc, 120)

    def _init_optional_tray(self) -> None:
        """Optional pystray integration. Without pystray, fallback is taskbar minimize."""
        try:
            import pystray  # type: ignore
            from PIL import Image, ImageDraw  # type: ignore
        except Exception:
            self._tray_available = False
            return
        try:
            image = Image.new("RGB", (64, 64), "#151821")
            draw = ImageDraw.Draw(image)
            draw.ellipse((8, 8, 56, 56), outline="#6EA8FE", width=4)
            draw.text((24, 18), "L", fill="#F3F6FF")

            def show_window(_icon=None, _item=None) -> None:
                self._post_to_ui(lambda: (self.deiconify(), self.lift()))

            def exit_app(icon=None, _item=None) -> None:
                self._post_to_ui(lambda: self._exit_application_from_tray(icon))

            self._tray_icon = pystray.Icon("linyuanzhe", image, "临渊者", menu=pystray.Menu(
                pystray.MenuItem("显示主窗口", show_window),
                pystray.MenuItem("退出", exit_app),
            ))
            self._tray_available = True
            self._tray_thread = threading.Thread(target=self._tray_icon.run, name="linyuanzhe-tray", daemon=True)
            self._tray_thread.start()
        except Exception as exc:
            self._tray_available = False
            self._record_ui_warning("optional_tray_init", exc, 120)

    def _exit_application_from_tray(self, icon: Any = None) -> None:
        try:
            self._persist_current_chat_history(getattr(self, "snapshot", RuntimeSnapshot()))
        except Exception as exc:
            self._record_ui_warning("tray_exit_persist", exc, 120)
        try:
            if icon is not None:
                icon.stop()
            elif getattr(self, "_tray_icon", None) is not None:
                self._tray_icon.stop()
        except Exception:
            pass
        try:
            self.destroy()
        except tk.TclError:
            pass

    def _on_close_window(self) -> None:
        try:
            self._persist_current_chat_history(getattr(self, "snapshot", RuntimeSnapshot()))
        except Exception as exc:
            self._record_ui_warning("close_persist_history", exc, 120)
        if bool(getattr(self, "minimize_to_tray_var", tk.BooleanVar(value=True)).get()):
            try:
                self.withdraw() if getattr(self, "_tray_available", False) else self.iconify()
                self.stream_status_var.set("窗口已最小化；托盘增强可用时进入系统托盘，否则进入任务栏。")
                return
            except tk.TclError as exc:
                self._record_ui_warning("close_minimize", exc, 120)
        self._exit_application_from_tray()

    # ------------------------------------------------------------------ shell
    def _build_shell(self) -> None:
        side_width = self._sidebar_width_for_current_window()
        self.grid_columnconfigure(0, minsize=side_width, weight=0)
        self.grid_columnconfigure(1, minsize=DIMENS.get("content_min_w", 640), weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_topbar()
        self._build_sidebar()
        self.content = tk.Frame(self, bg=COLORS["bg_root"])
        self.content.grid(row=1, column=1, sticky="nsew")
        self._build_statusbar()

    def _build_topbar(self) -> None:
        top = tk.Frame(self, bg=COLORS["bg_window"], height=DIMENS["topbar_h"])
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        top.grid_propagate(False)
        top.grid_columnconfigure(0, minsize=self._sidebar_width_for_current_window())
        top.grid_columnconfigure(1, weight=1)

        # L6.72.42: 顶栏只保留固定产品题头。Soul/persona 名字属于会话人格，
        # 不再顶替产品名；版本、模型、模式解释移出顶栏，减少视觉噪声。
        brand = tk.Label(
            top,
            text="天工造物V2",
            fg=COLORS["text_main"],
            bg=COLORS["bg_window"],
            font=FONTS["title"],
            anchor="w",
        )
        brand.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=6)

        spacer = tk.Frame(top, bg=COLORS["bg_window"])
        spacer.grid(row=0, column=1, sticky="nsew")

        # 新对话入口只保留在输入区控制条，右上角不再出现重复按钮。

    def _build_sidebar(self) -> None:
        if self._is_macos_surface():
            self._adaptive_sidebar_icon_mode = False
        else:
            self._adaptive_sidebar_icon_mode = self._current_window_width() < 1100
        side_width = self._sidebar_width_for_current_window()
        side = tk.Frame(self, bg=COLORS["bg_sidebar"], width=side_width)
        side.grid(row=1, column=0, sticky="nsew")
        side.grid_propagate(False)
        side.grid_columnconfigure(0, minsize=side_width, weight=1)
        side.grid_rowconfigure(len(PAGE_DEFINITIONS) + 1, weight=1)

        for i, spec in enumerate(PAGE_DEFINITIONS, start=0):
            # Use tk.Label instead of native tk.Button. On macOS Aqua, Button may
            # ignore custom bg/fg and render as blank white blocks after rebuilds.
            btn = tk.Label(
                side,
                text=self._sidebar_text_for_spec(spec),
                anchor="center" if getattr(self, "_adaptive_sidebar_icon_mode", False) else "w",
                relief="flat",
                bd=0,
                padx=8 if getattr(self, "_adaptive_sidebar_icon_mode", False) else 18,
                pady=9,
                font=FONTS["body"],
                cursor="hand2",
                bg=COLORS["bg_sidebar"],
                fg=COLORS["text_sub"],
            )
            btn.bind("<Button-1>", lambda _event, key=spec.key: self.show_page(key))
            btn.grid(row=i, column=0, sticky="ew", padx=6 if getattr(self, "_adaptive_sidebar_icon_mode", False) else 10, pady=(12 if i == 0 else 2, 0))
            self.nav_buttons[spec.key] = btn

    def _build_statusbar(self) -> None:
        bar = tk.Frame(self, bg=COLORS["bg_window"], height=DIMENS["statusbar_h"])
        bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)
        status_items = [
            ("runtime_status", "就绪"),
            ("backend_mode", "后端模式"),
            ("gate_status", "质量门"),
            ("audit_id", "审计"),
        ]
        for idx, (key, text) in enumerate(status_items):
            cluster = tk.Frame(bar, bg=COLORS["bg_window"])
            cluster.pack(side="left", padx=(12 if idx == 0 else 7, 7), pady=4)
            label = tk.Label(cluster, text=text, bg=COLORS["bg_window"], fg=COLORS["text_sub"], font=FONTS["small"])
            label.pack(side="left")
            self.status_labels[key] = label
            if idx < len(status_items) - 1:
                tk.Frame(bar, bg=COLORS["divider"], width=1, height=12).pack(side="left", pady=6)

        # Keep statusbar read-only. Theme choices live only in Settings / 字体与主题，
        # so the same visual page never shows duplicate theme selectors.
        spacer = tk.Frame(bar, bg=COLORS["bg_window"])
        spacer.pack(side="left", fill="x", expand=True)

    # --------------------------------------------------------------- navigation
    def show_page(self, page_key: str) -> None:
        if page_key not in PAGE_BY_KEY:
            page_key = DEFAULT_PAGE
        self.current_page = page_key
        try:
            # 设置页必须读取运行时最新模型服务投影，保证保存后
            # credentials/config digests are visible immediately after restart.
            # Other pages keep get_snapshot() to avoid unnecessary polling.
            if page_key == "settings":
                refresh = getattr(self.client, "refresh_snapshot", None)
                self.snapshot = refresh() if callable(refresh) else self.client.get_snapshot()
            else:
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
        page_root = self._prepare_page_root(page_key)
        if page_key == "chat":
            self._build_chat_page(page_root, self.snapshot)
        elif page_key == "execution":
            self._build_execution_page(page_root, self.snapshot)
        elif page_key == "observability":
            self._build_observability_page(page_root, self.snapshot)
        elif page_key == "sessions":
            self._build_sessions_page(page_root, self.snapshot)
        elif page_key == "history":
            self._build_history_page(page_root, self.snapshot)
        elif page_key == "files":
            self._build_files_page(page_root, self.snapshot)
        elif page_key == "workspace":
            self._build_workspace_page(page_root, self.snapshot)
        elif page_key == "connectors":
            self._build_connectors_page(page_root, self.snapshot)
        elif page_key == "hooks":
            self._build_hooks_page(page_root, self.snapshot)
        elif page_key == "memory":
            self._build_memory_page(page_root, self.snapshot)
        elif page_key == "iteration":
            self._build_iteration_page(page_root, self.snapshot)
        elif page_key == "four_paths":
            self._build_four_paths_page(page_root, self.snapshot)
        elif page_key == "installer":
            self._build_installer_page(page_root, self.snapshot)
        elif page_key == "settings":
            self._build_settings_page(page_root, self.snapshot)
        self._render_statusbar(self.snapshot)
        try:
            self._maybe_show_permission_popup(self.snapshot)
        except Exception as exc:
            self._record_ui_warning("permission_popup", exc, 120)
        if page_key == "chat":
            # Re-rendering the page during refresh used to reset Tk's Text
            # viewport to the first line. Keep manual refresh pinned to newest
            # 按桌面用户预期渲染运行时输出。
            self._force_chat_scroll_to_end()

    def refresh(self) -> None:
        self.show_page(self.current_page)

    def _post_to_ui(self, callback: Any) -> None:
        """Post a UI mutation from a worker thread to the Tk main thread.

        Tk calls such as after/createcommand are not safe from arbitrary worker
        threads on all Python/Tk builds. The stream worker therefore writes to a
        queue and the main thread drains it through an after timer.
        """
        try:
            self._ui_event_queue.put(callback)
        except Exception as exc:
            self._record_ui_warning("last_ui_queue_error", exc, 120)

    def _schedule_ui_event_drain(self) -> None:
        try:
            self.after(30, self._drain_ui_event_queue)
        except tk.TclError as exc:
            self._record_ui_warning("last_ui_drain_schedule_error", exc, 120)

    def _drain_ui_event_queue(self) -> None:
        drained = 0
        while drained < 128:
            try:
                callback = self._ui_event_queue.get_nowait()
            except queue.Empty:
                break
            try:
                callback()
            except tk.TclError as exc:
                self._record_ui_warning("last_ui_drain_tcl_error", exc, 120)
            except Exception as exc:
                self._record_ui_warning("last_ui_drain_error", exc, 120)
            drained += 1
        if self.winfo_exists():
            self._schedule_ui_event_drain()

    def _record_ui_warning(self, key: str, exc: Exception, limit: int = 120) -> None:
        self._ui_warning_log.append({"key": safe_text(key, 80), "message": safe_text(exc, limit)})
        self._ui_warning_log = self._ui_warning_log[-40:]

    def _sync_nav_state(self) -> None:
        for key, btn in self.nav_buttons.items():
            selected = key == self.current_page
            try:
                btn.configure(
                    bg=COLORS["selected"] if selected else COLORS["bg_sidebar"],
                    fg=COLORS["text_main"] if selected else COLORS["text_sub"],
                )
            except tk.TclError as exc:
                self._record_ui_warning("nav_state_apply", exc, 80)

    def _clear_content(self) -> None:
        self._unbind_page_mousewheel()
        # Tk widgets are destroyed during page switches; keep no stale chat/input
        # references. Streaming render may still receive queued snapshots after a
        # navigation event, so it must rebuild from the latest snapshot instead of
        # writing into a dead Text widget.
        self._chat_body_widget = None
        self._chat_render_signatures = []
        for attr in ("input_text", "input_placeholder_label"):
            if hasattr(self, attr):
                try:
                    delattr(self, attr)
                except AttributeError:
                    pass
        for child in self.content.winfo_children():
            child.destroy()
        self._page_scroll_canvas = None
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def _unbind_page_mousewheel(self) -> None:
        after_id = getattr(self, "_page_scroll_region_after_id", None)
        if after_id:
            try:
                self.after_cancel(after_id)
            except tk.TclError:
                pass
            self._page_scroll_region_after_id = None
        if not getattr(self, "_page_scroll_bind_active", False) and not getattr(self, "_wheel_bound_to_page", False):
            return
        try:
            self.unbind_all("<MouseWheel>")
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")
        finally:
            self._page_scroll_bind_active = False
            self._wheel_bound_to_page = False

    def _make_scrollable_page_root(self) -> tk.Frame:
        """Create a scrollable page surface for dense non-chat pages.

        L6.72.24 throttles scrollregion recalculation and only binds wheel
        events while the pointer is over the page canvas. This removes the
        Settings page jank caused by global wheel capture and repeated layout
        recalculation during every Configure event.
        """
        outer = tk.Frame(self.content, bg=COLORS["bg_root"])
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(0, weight=1)
        canvas = tk.Canvas(outer, bg=COLORS["bg_root"], highlightthickness=0, bd=0)
        vbar = make_vertical_scrollbar(outer, canvas.yview, variant="page")
        canvas.configure(yscrollcommand=vbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        inner = tk.Frame(canvas, bg=COLORS["bg_root"])
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def apply_region() -> None:
            self._page_scroll_region_after_id = None
            try:
                canvas.itemconfigure(window_id, width=max(1, canvas.winfo_width()))
                canvas.configure(scrollregion=canvas.bbox("all"))
            except tk.TclError as exc:
                self._record_ui_warning("last_page_scroll_error", exc, 120)

        def refresh_region(_event: tk.Event | None = None) -> None:
            if getattr(self, "_page_scroll_region_after_id", None):
                return
            try:
                self._page_scroll_region_after_id = self.after(24, apply_region)
            except tk.TclError:
                apply_region()

        def on_mousewheel(event: tk.Event) -> str:
            try:
                delta = getattr(event, "delta", 0)
                if delta:
                    steps = -1 if delta > 0 else 1
                    canvas.yview_scroll(steps * 5, "units")
                elif getattr(event, "num", None) == 4:
                    canvas.yview_scroll(-5, "units")
                elif getattr(event, "num", None) == 5:
                    canvas.yview_scroll(5, "units")
            except tk.TclError as exc:
                self._record_ui_warning("last_page_wheel_error", exc, 120)
            return "break"

        def bind_page_wheel(_event: tk.Event | None = None) -> None:
            if getattr(self, "_wheel_bound_to_page", False):
                return
            self.bind_all("<MouseWheel>", on_mousewheel)
            self.bind_all("<Button-4>", on_mousewheel)
            self.bind_all("<Button-5>", on_mousewheel)
            self._wheel_bound_to_page = True
            self._page_scroll_bind_active = True

        def unbind_page_wheel(_event: tk.Event | None = None) -> None:
            self._unbind_page_mousewheel()

        inner.bind("<Configure>", refresh_region)
        canvas.bind("<Configure>", refresh_region)
        canvas.bind("<Enter>", bind_page_wheel)
        canvas.bind("<Leave>", unbind_page_wheel)
        inner.bind("<Enter>", bind_page_wheel)
        inner.bind("<Leave>", unbind_page_wheel)
        self._page_scroll_canvas = canvas
        refresh_region()
        return inner

    def _prepare_page_root(self, page_key: str) -> tk.Frame:
        if page_key == "chat":
            return self.content
        return self._make_scrollable_page_root()

    # ------------------------------------------------------------------ home











    _INLINE_MD_RE = re.compile(r"(`[^`\n]+`|\*\*[^*\n]+\*\*|~~[^~\n]+~~|(?<!\*)\*[^*\n]+\*(?!\*)|(?<!_)_[^_\n]+_(?!_)|\$\$?[^$\n]+\$\$?|\[[^\]\n]+\]\([^\)\n]+\)|https?://\S+|sandbox:/\S+|\[\^?\d+\])")



















    # --------------------------------------------------------------- execution







    # ------------------------------------------------------------- sessions

    # --------------------------------------------------------- observability



    # ------------------------------------------------------------------- hooks




    # ------------------------------------------------------------- iteration

    # ------------------------------------------------------------- four paths

    # ------------------------------------------------------------- installer

    # ---------------------------------------------------------------- settings












    # -------------------------------------------------------------- DataUp








    # ---------------------------------------------------------- shared cards












    # ---------------------------------------------------------- detail dialogs










    # -------------------------------------------------------------- actions






































