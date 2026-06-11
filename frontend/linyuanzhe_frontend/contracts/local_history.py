from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Iterable, List, Mapping

try:
    from .runtime_snapshot import RuntimeSnapshot, safe_chat_text, safe_text
except Exception:  # pragma: no cover - import smoke fallback
    RuntimeSnapshot = Any  # type: ignore

    def safe_text(value: Any, max_len: int = 200) -> str:
        return str(value or "")[:max_len]

    def safe_chat_text(value: Any, max_len: int = 8000) -> str:
        return str(value or "")[:max_len]


LOCAL_HISTORY_SCHEMA = "tiangong.fe01.local_chat_history.l67222.v1"
EXPORT_SCHEMA = "tiangong.fe01.local_chat_export.l67222.v1"


def _project_root_from_here() -> Path:
    # contracts/local_history.py -> contracts -> linyuanzhe_frontend -> frontend -> project root
    return Path(__file__).resolve().parents[3]


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _safe_file_stem(value: str, fallback: str = "session") -> str:
    raw = safe_text(value, 120).strip() or fallback
    digest = hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw)[:48].strip("._-") or fallback
    return f"{clean}_{digest}"


def _message_to_mapping(message: Any) -> Dict[str, str]:
    if isinstance(message, Mapping):
        return {
            "role": safe_text(message.get("role", "assistant"), 32),
            "label": safe_text(message.get("label", message.get("name", "")), 64),
            "time": safe_text(message.get("time", message.get("timestamp", "")), 80),
            "text": safe_chat_text(message.get("text", message.get("content", "")), 16000),
        }
    return {
        "role": safe_text(getattr(message, "role", "assistant"), 32),
        "label": safe_text(getattr(message, "label", getattr(message, "name", "")), 64),
        "time": safe_text(getattr(message, "time", getattr(message, "timestamp", "")), 80),
        "text": safe_chat_text(getattr(message, "text", getattr(message, "content", "")), 16000),
    }


def _first_user_message(messages: Iterable[Mapping[str, str]]) -> str:
    for msg in messages:
        if safe_text(msg.get("role", ""), 32).lower() in {"user", "human"}:
            text = safe_chat_text(msg.get("text", ""), 500).strip().replace("\n", " ")
            return text or "未命名对话"
    for msg in messages:
        text = safe_chat_text(msg.get("text", ""), 500).strip().replace("\n", " ")
        if text:
            return text
    return "未命名对话"


def _date_bucket(ts: str) -> str:
    try:
        value = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except Exception:
        value = datetime.now().astimezone()
    today = datetime.now().astimezone().date()
    delta = (today - value.date()).days
    if delta <= 0:
        return "今天"
    if delta == 1:
        return "昨天"
    if delta <= 7:
        return "本周"
    return "更早"


@dataclass
class LocalHistoryRecord:
    session_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    path: str
    date_bucket: str
    preview: str = ""


@dataclass
class LocalChatHistoryStore:
    root: Path = field(default_factory=lambda: _project_root_from_here() / "workspace" / "chat_history")

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    def ensure_root(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root

    def _session_path(self, session_id: str) -> Path:
        return self.ensure_root() / (_safe_file_stem(session_id or "active-session") + ".json")

    def snapshot_to_payload(self, snapshot: RuntimeSnapshot) -> Dict[str, Any]:
        session_id = safe_text(getattr(snapshot, "session_id", "active-session"), 120) or "active-session"
        messages = [_message_to_mapping(item) for item in list(getattr(snapshot, "chat_messages", []) or [])]
        messages = [m for m in messages if safe_chat_text(m.get("text", ""), 16000).strip()]
        now = _now_iso()
        previous: Dict[str, Any] = {}
        path = self._session_path(session_id)
        if path.exists():
            try:
                previous = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                previous = {}
        title = safe_text(previous.get("title") or _first_user_message(messages), 100) or "未命名对话"
        payload = {
            "schema": LOCAL_HISTORY_SCHEMA,
            "session_id": session_id,
            "session_id_digest": hashlib.sha256(session_id.encode("utf-8", errors="ignore")).hexdigest()[:16],
            "title": title,
            "created_at": safe_text(previous.get("created_at", now), 80) or now,
            "updated_at": now,
            "source_kind": safe_text(getattr(snapshot, "source_kind", "runtime_snapshot"), 80),
            "provider": safe_text(getattr(snapshot, "model_provider", ""), 80),
            "model": safe_text(getattr(snapshot, "provider_model", ""), 120),
            "message_count": len(messages),
            "messages": messages,
        }
        return payload

    def payload_digest(self, payload: Mapping[str, Any]) -> str:
        minimal = {
            "session_id": payload.get("session_id", ""),
            "message_count": payload.get("message_count", 0),
            "messages": payload.get("messages", []),
        }
        return hashlib.sha256(json.dumps(minimal, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

    def save_snapshot(self, snapshot: RuntimeSnapshot) -> Path | None:
        payload = self.snapshot_to_payload(snapshot)
        if int(payload.get("message_count", 0) or 0) <= 0:
            return None
        path = self._session_path(safe_text(payload.get("session_id", "active-session"), 120))
        tmp_name = ""
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=str(path.parent), prefix=path.stem + ".", suffix=".tmp") as tmp:
            tmp_name = tmp.name
            json.dump(payload, tmp, ensure_ascii=False, indent=2)
            tmp.write("\n")
        Path(tmp_name).replace(path)
        return path

    def _load_payload(self, path: Path) -> Dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def list_records(self, query: str = "", limit: int = 200) -> List[LocalHistoryRecord]:
        self.ensure_root()
        q = safe_text(query, 120).lower().strip()
        records: List[LocalHistoryRecord] = []
        for path in sorted(self.root.glob("*.json"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True):
            data = self._load_payload(path)
            if data.get("schema") != LOCAL_HISTORY_SCHEMA:
                continue
            messages = list(data.get("messages", []) or [])
            title = safe_text(data.get("title") or _first_user_message(messages), 100)
            joined = " ".join(safe_chat_text(m.get("text", ""), 300) for m in messages if isinstance(m, Mapping)).lower()
            if q and q not in title.lower() and q not in joined:
                continue
            updated = safe_text(data.get("updated_at", ""), 80) or _now_iso()
            preview = safe_chat_text(_first_user_message(messages), 120)
            records.append(LocalHistoryRecord(
                session_id=safe_text(data.get("session_id", path.stem), 120),
                title=title or "未命名对话",
                created_at=safe_text(data.get("created_at", updated), 80),
                updated_at=updated,
                message_count=int(data.get("message_count", len(messages)) or 0),
                path=str(path),
                date_bucket=_date_bucket(updated),
                preview=preview,
            ))
            if len(records) >= limit:
                break
        return records

    def read_session(self, session_id: str) -> Dict[str, Any]:
        target_id = safe_text(session_id, 120)
        for path in self.ensure_root().glob("*.json"):
            data = self._load_payload(path)
            if safe_text(data.get("session_id", ""), 120) == target_id:
                return data
        path = self._session_path(target_id)
        return self._load_payload(path) if path.exists() else {}

    def render_markdown(self, payload: Mapping[str, Any]) -> str:
        title = safe_text(payload.get("title", "未命名对话"), 120)
        lines = [f"# {title}", "", f"- 导出时间：{_now_iso()}", f"- 消息数：{int(payload.get('message_count', 0) or 0)}", ""]
        for msg in list(payload.get("messages", []) or []):
            if not isinstance(msg, Mapping):
                continue
            role = "用户" if safe_text(msg.get("role", ""), 32).lower() in {"user", "human"} else "AI"
            time_text = safe_text(msg.get("time", ""), 80)
            lines.append(f"## {role}" + (f" · {time_text}" if time_text else ""))
            lines.append("")
            lines.append(safe_chat_text(msg.get("text", ""), 16000).rstrip())
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def render_text(self, payload: Mapping[str, Any]) -> str:
        title = safe_text(payload.get("title", "未命名对话"), 120)
        lines = [title, "=" * max(4, min(60, len(title))), f"导出时间：{_now_iso()}", ""]
        for msg in list(payload.get("messages", []) or []):
            if not isinstance(msg, Mapping):
                continue
            role = "用户" if safe_text(msg.get("role", ""), 32).lower() in {"user", "human"} else "AI"
            lines.append(f"[{role}] {safe_text(msg.get('time', ''), 80)}".rstrip())
            lines.append(safe_chat_text(msg.get("text", ""), 16000).rstrip())
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def export_session(self, session_id: str, fmt: str, target_dir: Path) -> Path:
        payload = self.read_session(session_id)
        if not payload:
            raise FileNotFoundError("未找到本地历史会话")
        fmt = safe_text(fmt, 20).lower()
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        stem = _safe_file_stem(safe_text(payload.get("title") or session_id, 80), "chat_export")
        if fmt == "json":
            out = dict(payload)
            out["export_schema"] = EXPORT_SCHEMA
            path = target_dir / f"{stem}.json"
            path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return path
        if fmt in {"md", "markdown"}:
            path = target_dir / f"{stem}.md"
            path.write_text(self.render_markdown(payload), encoding="utf-8")
            return path
        if fmt in {"txt", "text"}:
            path = target_dir / f"{stem}.txt"
            path.write_text(self.render_text(payload), encoding="utf-8")
            return path
        raise ValueError(f"不支持的导出格式：{fmt}")

    def clear_all(self) -> int:
        self.ensure_root()
        count = 0
        for path in list(self.root.glob("*.json")):
            try:
                path.unlink()
                count += 1
            except FileNotFoundError:
                pass
        cache_dir = self.root.parent / "cache"
        if cache_dir.exists() and cache_dir.is_dir():
            shutil.rmtree(cache_dir, ignore_errors=True)
        return count
