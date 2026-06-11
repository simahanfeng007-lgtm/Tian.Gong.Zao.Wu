from __future__ import annotations

import json
import sys
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
        body = app._chat_body_widget
        tag_names = set(body.tag_names()) if body is not None else set()
        tag_ranges = {name: bool(body.tag_ranges(name)) if body is not None else False for name in tag_names}
        transcript = "\n".join(getattr(m, "text", "") for m in app.snapshot.chat_messages)
        checks = {
            "markdown_tags_configured": all(name in tag_names for name in [
                "md_heading1", "md_bold", "md_list", "md_code_block", "md_inline_code", "md_link"
            ]),
            "heading_rendered": tag_ranges.get("md_heading1", False),
            "bold_rendered": tag_ranges.get("md_bold", False),
            "list_rendered": tag_ranges.get("md_list", False),
            "code_block_rendered": tag_ranges.get("md_code_block", False),
            "inline_code_rendered": tag_ranges.get("md_inline_code", False),
            "link_recognized": tag_ranges.get("md_link", False),
            "chat_newlines_preserved": "\n" in transcript,
            "no_frontend_execution_claim": "frontend_execution" in transcript and "false" in transcript,
        }
        ok = all(checks.values())
        payload = {
            "schema": "tiangong.fe01.step31m.markdown_acceptance.v1",
            "ok": ok,
            "checks": checks,
            "note": "Tk Text tag ranges verify Markdown readability without running Runtime, Provider SDKs, tools, memory or audit writes.",
        }
        (report_dir / "step31m_markdown_acceptance.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return 0 if ok else 1
    finally:
        app.destroy()


if __name__ == "__main__":
    raise SystemExit(main())
