from __future__ import annotations

import json
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
from linyuanzhe_frontend.contracts.model_settings import DEFAULT_MODEL_CATALOG, filter_model_catalog, sanitize_runtime_settings
from linyuanzhe_frontend.contracts.provider_settings import provider_readiness_from_public_projection
from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot, StepSummary, digest_text, safe_chat_text, safe_text
from linyuanzhe_frontend.contracts.streaming_render import RenderScheduler
from linyuanzhe_frontend.version_info import FE_BADGE, FE_TITLE, PROVIDER_CONFIG_SCHEMA_VERSION
from .page_specs import ALL_PAGE_DEFINITIONS, DEFAULT_PAGE, PAGE_BY_KEY, PAGE_DEFINITIONS
from .theme import COLORS, DIMENS, FONTS, STATUS_COLORS, THEME_PROFILES, apply_theme_profile
from .widgets import Card, Chip, MetricRow, StepItem, LabeledValue, StatusPill, configure_ttk_style, make_button, make_hint, make_readonly_banner, make_section_title
from .main_window_chat_runtime import ChatRuntimeMixin
from .main_window_feature_pages import FeaturePagesMixin
from .main_window_actions import FrontendActionsMixin


class LinyuanzheDesktopApp(tk.Tk, ChatRuntimeMixin, FeaturePagesMixin, FrontendActionsMixin):
    """FE.01 desktop shell.

    STEP10B locks the corrected homepage into a cleaner desktop presentation:
    chat-first center workspace, fixed input bar, minimal right-side status summary,
    and progressive disclosure for execution details. It still only reads Mock/JSON
    projections and records frontend-only confirmation state.
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
        self.nav_buttons: Dict[str, tk.Button] = {}
        self.status_labels: Dict[str, tk.Label] = {}
        self.theme_buttons: Dict[str, tk.Button] = {}
        self._page_scroll_canvas: tk.Canvas | None = None
        self._page_scroll_bind_active = False
        self.session_info_expanded = False
        self.api_provider_var = tk.StringVar(value="openai_compatible")
        self.api_base_url_var = tk.StringVar(value="")
        self.api_key_var = tk.StringVar(value="")
        self.main_model_var = tk.StringVar(value="deepseek-v4-pro")
        self.model_search_var = tk.StringVar(value="")
        self.session_search_var = tk.StringVar(value="")
        self.selected_session_id = ""
        self.theme_profile_var = tk.StringVar(value=self._load_ui_preferences().get("theme_profile", "midnight"))
        apply_theme_profile(self.theme_profile_var.get())
        self.connector_status_var = tk.StringVar(value="连接器注册：等待提交")
        self.file_auto_run_var = tk.BooleanVar(value=True)
        self.installer_status_var = tk.StringVar(value="启动自检：等待运行")
        self.dataup_status_var = tk.StringVar(value="DataUp：等待检查；前端只启动安全更新器，不直接覆盖文件。")
        self.settings_status_var = tk.StringVar(value="API 与主模型设置仅在设置页维护；Key/Base URL 写入后仅保留 digest。")
        self.settings_save_feedback_var = tk.StringVar(value="")
        self._settings_feedback_after_id: str | None = None
        self.stream_status_var = tk.StringVar(value="流式状态：idle")
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
        self._stream_lock = threading.Lock()
        self._render_scheduler = RenderScheduler(min_interval_ms=24)
        self._pending_stream_snapshot: RuntimeSnapshot | None = None
        self._pending_stream_finished = False
        self._render_after_id: str | None = None
        self._chat_body_widget: tk.Text | None = None
        self._chat_render_signatures: List[tuple[str, str, str, str]] = []
        self._ui_event_queue: queue.Queue[Any] = queue.Queue()
        self.title(FE_TITLE)
        self.geometry(f"{DIMENS['window_w']}x{DIMENS['window_h']}")
        self.minsize(DIMENS["window_min_w"], DIMENS["window_min_h"])
        self.configure(bg=COLORS["bg_root"])
        configure_ttk_style(self)
        self._build_shell()
        self.bind("<F5>", lambda _event: self._refresh_snapshot_frontend_only())
        self.bind("<Control-r>", lambda _event: self._request_session_resume_active())
        self.bind("<Control-f>", lambda _event: self.show_page("sessions"))
        self.bind("<Control-period>", lambda _event: self._request_task_interrupt())
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
            payload = {"schema": "tiangong.fe01.ui_preferences.v1", "theme_profile": self.theme_profile_var.get()}
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            self._record_ui_warning("last_ui_preferences_error", exc, 160)

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
        frontend theme preference and does not touch Runtime, Provider, memory,
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
        top.grid_propagate(False)
        top.grid_columnconfigure(0, minsize=DIMENS["sidebar_w"])
        top.grid_columnconfigure(1, weight=1)

        brand = tk.Label(
            top,
            text="临渊者",
            fg=COLORS["text_main"],
            bg=COLORS["bg_window"],
            font=FONTS["title"],
            anchor="w",
        )
        brand.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=8)

        context = tk.Frame(top, bg=COLORS["bg_window"])
        context.grid(row=0, column=1, sticky="w", pady=8)
        Chip(context, FE_BADGE, "gray").pack(side="left")
        tk.Label(
            context,
            text="Provider 状态清楚 · 对话优先",
            bg=COLORS["bg_window"],
            fg=COLORS["text_weak"],
            font=FONTS["small"],
        ).pack(side="left", padx=(10, 0))

        actions = [("新会话", self._new_task_frontend_only), ("设置", lambda: self.show_page("settings"))]
        for idx, (text, command) in enumerate(actions):
            variant = "primary" if idx == 0 else "secondary"
            btn = make_button(top, text, command, variant=variant, padx=12, pady=5)
            btn.grid(row=0, column=2 + idx, padx=(0, 10), pady=8)

    def _build_sidebar(self) -> None:
        side = tk.Frame(self, bg=COLORS["bg_sidebar"], width=DIMENS["sidebar_w"])
        side.grid(row=1, column=0, sticky="nsw")
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)
        side.grid_rowconfigure(len(PAGE_DEFINITIONS) + 1, weight=1)

        for i, spec in enumerate(PAGE_DEFINITIONS, start=0):
            btn = tk.Button(
                side,
                text=safe_text(spec.label, 24),
                anchor="w",
                command=lambda key=spec.key: self.show_page(key),
                relief="flat",
                bd=0,
                padx=18,
                pady=9,
                font=FONTS["body"],
                cursor="hand2",
            )
            btn.grid(row=i, column=0, sticky="ew", padx=10, pady=(12 if i == 0 else 2, 0))
            self.nav_buttons[spec.key] = btn

    def _build_statusbar(self) -> None:
        bar = tk.Frame(self, bg=COLORS["bg_window"], height=DIMENS["statusbar_h"])
        bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)
        status_items = [
            ("runtime_status", "就绪"),
            ("backend_mode", "模式"),
            ("gate_status", "质量门"),
            ("audit_id", "审计"),
        ]
        for idx, (key, text) in enumerate(status_items):
            cluster = tk.Frame(bar, bg=COLORS["bg_window"])
            cluster.pack(side="left", padx=(14 if idx == 0 else 8, 8), pady=7)
            label = tk.Label(cluster, text=text, bg=COLORS["bg_window"], fg=COLORS["text_sub"], font=FONTS["small"])
            label.pack(side="left")
            self.status_labels[key] = label
            if idx < len(status_items) - 1:
                tk.Frame(bar, bg=COLORS["divider"], width=1, height=14).pack(side="left", pady=9)

        # Right side: compact theme switch requested for the bottom frame.
        # Only two high-frequency choices are exposed here; the full appearance
        # list remains in Settings.
        spacer = tk.Frame(bar, bg=COLORS["bg_window"])
        spacer.pack(side="left", fill="x", expand=True)
        theme_box = tk.Frame(bar, bg=COLORS["bg_window"])
        theme_box.pack(side="right", padx=(8, 14), pady=4)
        tk.Label(theme_box, text="主题", bg=COLORS["bg_window"], fg=COLORS["text_weak"], font=FONTS["small"]).pack(side="left", padx=(0, 6))
        for profile, label in (("midnight", "永夜"), ("warm_gray", "极昼")):
            btn = tk.Button(
                theme_box,
                text=label,
                command=lambda p=profile: self._set_theme_profile(p),
                bg=COLORS["bg_card_2"],
                fg=COLORS["text_sub"],
                activebackground=COLORS["selected"],
                activeforeground=COLORS["text_main"],
                relief="flat",
                bd=0,
                padx=9,
                pady=2,
                cursor="hand2",
                font=FONTS["small"],
            )
            btn.pack(side="left", padx=(0, 4))
            self.theme_buttons[profile] = btn
        self._refresh_theme_switch_buttons()

    # --------------------------------------------------------------- navigation
    def show_page(self, page_key: str) -> None:
        if page_key not in PAGE_BY_KEY:
            page_key = DEFAULT_PAGE
        self.current_page = page_key
        try:
            # Settings page must read Runtime's latest provider projection so saved
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
        if page_key == "chat":
            # Re-rendering the page during refresh used to reset Tk's Text
            # viewport to the first line. Keep manual refresh pinned to newest
            # Runtime output as requested by desktop users.
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
            btn.configure(
                bg=COLORS["selected"] if selected else COLORS["bg_sidebar"],
                fg=COLORS["text_main"] if selected else COLORS["text_sub"],
                activebackground=COLORS["selected"],
                activeforeground=COLORS["text_main"],
            )

    def _clear_content(self) -> None:
        self._unbind_page_mousewheel()
        for child in self.content.winfo_children():
            child.destroy()
        self._page_scroll_canvas = None
        self._chat_body_widget = None
        self._chat_render_signatures = []
        self.input_text = None
        self.input_placeholder_label = None
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def _unbind_page_mousewheel(self) -> None:
        if not getattr(self, "_page_scroll_bind_active", False):
            return
        try:
            self.unbind_all("<MouseWheel>")
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")
        finally:
            self._page_scroll_bind_active = False

    def _make_scrollable_page_root(self) -> tk.Frame:
        """Create a scrollable page surface for dense non-chat pages.

        Human-size windows clip lower cards on execution/session/workspace pages
        unless the whole page can scroll. The chat page keeps its own transcript
        scroller, but every other page uses this outer canvas.
        """
        outer = tk.Frame(self.content, bg=COLORS["bg_root"])
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(0, weight=1)
        canvas = tk.Canvas(outer, bg=COLORS["bg_root"], highlightthickness=0, bd=0)
        vbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview, bg=COLORS["bg_card"], troughcolor=COLORS["bg_root"])
        canvas.configure(yscrollcommand=vbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        inner = tk.Frame(canvas, bg=COLORS["bg_root"])
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def refresh_region(_event: tk.Event | None = None) -> None:
            try:
                canvas.itemconfigure(window_id, width=max(1, canvas.winfo_width()))
                canvas.configure(scrollregion=canvas.bbox("all"))
            except tk.TclError as exc:
                self._record_ui_warning("last_page_scroll_error", exc, 120)

        def on_mousewheel(event: tk.Event) -> str:
            try:
                delta = getattr(event, "delta", 0)
                if delta:
                    canvas.yview_scroll(int(-1 * (delta / 120)), "units")
                elif getattr(event, "num", None) == 4:
                    canvas.yview_scroll(-3, "units")
                elif getattr(event, "num", None) == 5:
                    canvas.yview_scroll(3, "units")
            except tk.TclError as exc:
                self._record_ui_warning("last_page_wheel_error", exc, 120)
            return "break"

        inner.bind("<Configure>", refresh_region)
        canvas.bind("<Configure>", refresh_region)
        self.bind_all("<MouseWheel>", on_mousewheel)
        self.bind_all("<Button-4>", on_mousewheel)
        self.bind_all("<Button-5>", on_mousewheel)
        self._page_scroll_bind_active = True
        self._page_scroll_canvas = canvas
        return inner

    def _prepare_page_root(self, page_key: str) -> tk.Frame:
        if page_key == "chat":
            return self.content
        return self._make_scrollable_page_root()

    # ------------------------------------------------------------------ home











    _INLINE_MD_RE = re.compile(r"(`[^`\n]+`|\*\*[^*\n]+\*\*|\[[^\]\n]+\]\([^\)\n]+\)|https?://\S+)")



















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






































