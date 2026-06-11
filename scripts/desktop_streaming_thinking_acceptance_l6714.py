from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

from linyuanzhe_frontend.clients.mock_runtime_client import MockRuntimeClient
from linyuanzhe_frontend.ui.main_window import LinyuanzheDesktopApp


def main() -> int:
    report_dir = ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    app = LinyuanzheDesktopApp(MockRuntimeClient())
    try:
        app.show_page("chat")
        app.update_idletasks()
        baseline_full_rebuild = getattr(app, "_chat_full_rebuild_count", 0)
        ok_submit = app._submit_text_to_runtime_stream("请用 Markdown 演示一次流式输出。")
        deadline = time.time() + 4.0
        while time.time() < deadline:
            app.update()
            worker = getattr(app, "_stream_worker", None)
            if worker is None or not worker.is_alive():
                # Drain queued callbacks scheduled by the stream worker.
                for _ in range(6):
                    app.update()
                    time.sleep(0.02)
                break
            time.sleep(0.02)
        body = app._chat_body_widget
        transcript_text = body.get("1.0", "end") if body is not None else ""
        history = list(getattr(app, "_live_indicator_history", []) or [])
        checks = {
            "submit_started": bool(ok_submit),
            "stream_completed": getattr(app.snapshot, "stream_state", "") == "completed",
            "thinking_indicator_seen": "正在思考" in history,
            "streaming_indicator_seen": "正在输出" in history,
            "markdown_stream_visible": "Mock 流式演示" in transcript_text and "frontend_execution=false" in transcript_text,
            "no_full_rebuild_after_submit": getattr(app, "_chat_full_rebuild_count", 0) <= baseline_full_rebuild + 1,
            "last_message_rewritten_incrementally": getattr(app, "_chat_rewrite_last_count", 0) >= 1,
            "append_path_used": getattr(app, "_chat_append_count", 0) >= 2,
            "frontend_boundary_visible": "runtime_only=true" in transcript_text,
        }
        payload = {
            "schema": "tiangong.fe01.step31n.streaming_thinking_acceptance.v1",
            "ok": all(checks.values()),
            "checks": checks,
            "render_counters": {
                "full_rebuild": getattr(app, "_chat_full_rebuild_count", 0),
                "rewrite_last": getattr(app, "_chat_rewrite_last_count", 0),
                "append": getattr(app, "_chat_append_count", 0),
                "baseline_full_rebuild": baseline_full_rebuild,
            },
            "indicator_history": history,
            "note": "Mock streaming validates thinking state and incremental Tk rendering only. No Runtime tool, Provider SDK, memory write, audit write or QualityGate bypass is executed.",
        }
        (report_dir / "step31n_streaming_thinking_acceptance.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return 0 if payload["ok"] else 1
    finally:
        app.destroy()


if __name__ == "__main__":
    raise SystemExit(main())
