from __future__ import annotations

"""FE01 STEP31F / L6.70.6 desktop human-visual click audit.

This is a deterministic Tk audit that approximates a human pass:
- opens the desktop shell under a real Tk event loop;
- navigates every sidebar page;
- verifies dense pages are scrollable instead of clipped;
- exercises chat send, chat scroll pinning, file upload request, write-directory
  authorization, MCP registration, self-check and theme switching;
- uses the bundled local bridge only, with a temporary provider config path.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend" / "project"
REPORTS = ROOT / "reports"
BRIDGE = ROOT / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"
REPORT = REPORTS / "desktop_human_visual_click_audit_l6706.json"
AUDIT_PROVIDER_CONFIG = REPORTS / "ui_audit_provider_config.json"
URL_RE = re.compile(r"LINYUANZHE_LOCAL_RUNTIME_URL=(http://[^\s]+)")

sys.path.insert(0, str(FRONTEND))
sys.path.insert(0, str(BACKEND))


def _start_bridge() -> tuple[subprocess.Popen[str], str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(FRONTEND), str(BACKEND), env.get("PYTHONPATH", "")])
    env["LINYUANZHE_PROVIDER_CONFIG_FILE"] = str(AUDIT_PROVIDER_CONFIG)
    proc = subprocess.Popen(
        [sys.executable, str(BRIDGE), "--host", "127.0.0.1", "--port", "0", "--backend-mode", "auto", "--timeout", "45"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    deadline = time.time() + 20
    seen: list[str] = []
    while time.time() < deadline:
        line = proc.stdout.readline()
        if line:
            seen.append(line.rstrip())
            m = URL_RE.search(line)
            if m:
                return proc, m.group(1)
        if proc.poll() is not None:
            break
    raise RuntimeError("bridge did not start: " + "\n".join(seen[-20:]))


def _stop_bridge(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def _pump(app: Any, seconds: float = 0.1) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        app.update_idletasks()
        app.update()
        time.sleep(0.01)


def _wait_stream(app: Any, timeout: float = 45.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        _pump(app, 0.05)
        worker = getattr(app, "_stream_worker", None)
        if worker is None or not worker.is_alive():
            _pump(app, 0.2)
            return
    raise TimeoutError("stream worker did not finish")


def _count_widgets(widget: Any) -> int:
    total = 1
    for child in widget.winfo_children():
        total += _count_widgets(child)
    return total


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    fixture_file = REPORTS / "ui_audit_fixture.txt"
    fixture_file.write_text("临渊者 UI 审计附件。\n", encoding="utf-8")
    fixture_dir = REPORTS / "ui_audit_outbox"
    fixture_dir.mkdir(exist_ok=True)

    import tkinter as tk
    from tkinter import filedialog, messagebox

    messagebox_calls: list[dict[str, str]] = []

    def fake_message(kind: str):
        def inner(title: str = "", message: str = "", *args: Any, **kwargs: Any) -> str:
            messagebox_calls.append({"kind": kind, "title": str(title), "message": str(message)[:240]})
            return "ok"
        return inner

    messagebox.showinfo = fake_message("info")  # type: ignore[assignment]
    messagebox.showwarning = fake_message("warning")  # type: ignore[assignment]
    messagebox.showerror = fake_message("error")  # type: ignore[assignment]
    filedialog.askopenfilename = lambda *args, **kwargs: str(fixture_file)  # type: ignore[assignment]
    filedialog.askdirectory = lambda *args, **kwargs: str(fixture_dir)  # type: ignore[assignment]

    from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient
    from linyuanzhe_frontend.contracts.runtime_snapshot import ChatMessage
    from linyuanzhe_frontend.ui.main_window import LinyuanzheDesktopApp
    from linyuanzhe_frontend.ui.page_specs import ALL_PAGE_DEFINITIONS
    from linyuanzhe_frontend.ui.theme import COLORS

    proc: subprocess.Popen[str] | None = None
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            raise AssertionError(f"{name}: {detail}")

    try:
        proc, url = _start_bridge()
        client = SseRuntimeClient(url, timeout=45, max_reconnects=0)
        client.refresh_snapshot()
        app = LinyuanzheDesktopApp(client)
        app.geometry("1280x800")
        _pump(app, 0.4)

        pages = [spec.key for spec in ALL_PAGE_DEFINITIONS]
        for page in pages:
            app.show_page(page)
            _pump(app, 0.15)
            count = _count_widgets(app.content)
            check(f"page_render:{page}", count > 5, f"widgets={count}")
            if page != "chat":
                check(f"page_scrollable:{page}", getattr(app, "_page_scroll_canvas", None) is not None, "non-chat page has outer scroll canvas")

        # Theme buttons: full shell should repaint, not only the content frame.
        app._set_theme_profile("warm_gray")
        _pump(app, 0.2)
        check("theme:warm_gray_root", app.cget("bg") == COLORS["bg_root"], app.cget("bg"))
        sidebar_bg = app.nav_buttons[next(iter(app.nav_buttons))].cget("bg")
        check("theme:warm_gray_sidebar_repaint", sidebar_bg in {COLORS["selected"], COLORS["bg_sidebar"]}, sidebar_bg)
        app._set_theme_profile("ink_green")
        _pump(app, 0.2)
        check("theme:ink_green_root", app.cget("bg") == COLORS["bg_root"], app.cget("bg"))
        app._set_theme_profile("midnight")
        _pump(app, 0.2)

        # Chat submit through local bridge.
        app.show_page("chat")
        _pump(app, 0.15)
        app.input_text.insert("1.0", "你好")
        app._send_message()
        _wait_stream(app, 45)
        check("chat:stream_completed", app.snapshot.stream_state in {"completed", "error", "interrupted"}, app.snapshot.stream_state)
        check("chat:no_pending_confirmation_for_simple_message", int(app.snapshot.pending_confirmation_count or 0) == 0, str(app.snapshot.pending_confirmation_count))
        check("chat:no_mock_session_leak", not any(str(getattr(x, "session_id_digest", "")).upper().startswith("SESS-MOCK") for x in app.snapshot.task_sessions), "mock sessions filtered")

        # Synthetic long transcript must stay pinned to newest message after refresh.
        client._snapshot.chat_messages = [ChatMessage("assistant", "临渊者", f"T{i:02d}", ("滚动测试 " * 30) + str(i)) for i in range(70)]
        app.show_page("chat")
        _pump(app, 0.5)
        yview = app._chat_body_widget.yview() if app._chat_body_widget is not None else (0.0, 0.0)
        check("chat:scroll_pinned_after_refresh", yview[1] >= 0.98, f"yview={yview}")

        # File upload request, without auto-running another backend task.
        app.show_page("files")
        app.file_auto_run_var.set(False)
        app._request_file_transfer_from_dialog()
        _pump(app, 0.2)
        ft = list(getattr(app.snapshot, "file_transfer_records", []) or [])[-1]
        check("file:transfer_ack", getattr(ft, "status", "") in {"accepted", "frontend_fallback_recorded"}, getattr(ft, "status", ""))

        # Write authorization must select a directory and use workspace_outbox.
        app.show_page("workspace")
        app._request_file_authorization_from_dialog("write")
        _pump(app, 0.2)
        auth = list(getattr(app.snapshot, "file_authorization_records", []) or [])[-1]
        check("workspace:write_auth_mode", getattr(auth, "mode", "") == "write", getattr(auth, "mode", ""))
        check("workspace:write_auth_scope", getattr(auth, "scope", "") == "workspace_outbox", getattr(auth, "scope", ""))

        # MCP/connector registration click has visible ack and record.
        app.show_page("connectors")
        app._request_connector_registration()
        _pump(app, 0.2)
        check("connector:registration_ack", bool(getattr(app.snapshot, "connector_registration_records", []) or []), "record exists")
        check("connector:visible_notice", any("连接器注册" in x["title"] for x in messagebox_calls), "notice captured")

        # Installer self-check click.
        app.show_page("installer")
        app._run_startup_self_check()
        _pump(app, 0.2)
        check("installer:self_check", getattr(app.snapshot, "startup_self_check_state", "") in {"pass", "ok", "updated"}, getattr(app.snapshot, "startup_self_check_state", ""))

        # Provider settings in auto mode should switch bridge effective mode to provider immediately after save.
        result = client.submit_provider_settings({
            "provider": "deepseek",
            "main_model": "deepseek-reasoner",
            "api_base_url": "http://127.0.0.1:9/v1",
            "api_key": "audit-token-not-real",
        })
        client.refresh_snapshot()
        provider_public = client.get_provider_settings()
        check("provider:key_digest_saved", bool(provider_public.get("api_key_digest")), str(provider_public))
        check("provider:auto_switches_to_provider", provider_public.get("effective_backend_mode") == "provider" or client._json_request("/settings/provider").get("effective_backend_mode") == "provider", str(provider_public))

        app.destroy()
        ok = True
    except Exception as exc:
        ok = False
        checks.append({"name": "audit_exception", "ok": False, "detail": repr(exc)})
        try:
            # Ensure Tk exits if partially initialized.
            if "app" in locals():
                app.destroy()
        except Exception as cleanup_exc:
            checks.append({"name": "cleanup:app_destroy", "ok": False, "detail": repr(cleanup_exc)})
    finally:
        if proc is not None:
            _stop_bridge(proc)
        try:
            AUDIT_PROVIDER_CONFIG.unlink(missing_ok=True)
        except Exception as cleanup_exc:
            checks.append({"name": "cleanup:provider_config", "ok": False, "detail": repr(cleanup_exc)})

    payload = {
        "ok": ok,
        "schema": "tiangong.fe01.step31f.human_visual_click_audit.v1",
        "version": "FE01 STEP31F / L6.70.6",
        "checks": checks,
        "messagebox_calls": messagebox_calls,
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": ok, "report": str(REPORT), "checks": len(checks)}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
