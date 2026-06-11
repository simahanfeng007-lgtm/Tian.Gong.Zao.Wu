from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import json
import tempfile
from pathlib import Path

from linyuanzhe_frontend.contracts.local_history import LOCAL_HISTORY_SCHEMA, LocalChatHistoryStore
from linyuanzhe_frontend.contracts.runtime_snapshot import ChatMessage, RuntimeSnapshot
from linyuanzhe_frontend.ui.page_specs import PAGE_BY_KEY
from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="linyuanzhe_history_smoke_") as tmp:
        store = LocalChatHistoryStore(Path(tmp) / "workspace" / "chat_history")
        snap = RuntimeSnapshot(session_id="smoke-session-l67222", source_kind="smoke")
        snap.chat_messages = [
            ChatMessage("user", "你", "10:00", "请做一个历史导出测试。"),
            ChatMessage("assistant", "临渊者", "10:01", "收到。```python\nprint('ok')\n```"),
        ]
        path = store.save_snapshot(snap)
        _assert(path is not None and path.exists(), "history snapshot not saved")
        data = json.loads(path.read_text(encoding="utf-8"))
        _assert(data.get("schema") == LOCAL_HISTORY_SCHEMA, "history schema mismatch")
        records = store.list_records("历史导出")
        _assert(len(records) == 1, "history search failed")
        export_dir = Path(tmp) / "exports"
        md = store.export_session("smoke-session-l67222", "md", export_dir)
        txt = store.export_session("smoke-session-l67222", "txt", export_dir)
        js = store.export_session("smoke-session-l67222", "json", export_dir)
        _assert(md.suffix == ".md" and "```python" in md.read_text(encoding="utf-8"), "markdown export failed")
        _assert(txt.suffix == ".txt" and "用户" in txt.read_text(encoding="utf-8"), "text export failed")
        _assert(js.suffix == ".json" and json.loads(js.read_text(encoding="utf-8")).get("export_schema"), "json export failed")
        _assert("history" in PAGE_BY_KEY, "history page not registered")
        _assert((FE_RUNTIME_VERSION.startswith(("L6.72.", "L6.73.")) or FE_RUNTIME_VERSION.startswith("L6.73.")), "version not bumped")
        cleared = store.clear_all()
        _assert(cleared >= 1 and not list(store.root.glob("*.json")), "clear all failed")
    print("PASS desktop_history_export_tray_smoke_l67222")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
