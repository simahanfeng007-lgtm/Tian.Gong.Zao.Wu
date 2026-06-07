"""L6.40 MemoryStoreBridge：append-only JSONL 记忆存储桥。

边界：
- 属于 runtime 外壳层，不被 tiangong_kernel 引用；
- 只保存 sanitized_summary、digest、evidence refs 和治理字段；
- 不保存原始 prompt、密钥、完整隐私、完整文件正文；
- mark_tombstone / suppress_active_recall 追加事件，不物理删除；
- 物理删除只生成 delete_review 需求，不在本桥直接执行。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4
import hashlib
import json

from tiangong_agent_shell.safe_logging import redact_text
from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score

from .memory_math_core import MemoryCategory, MemoryLevel, elapsed_since, level_weight, success_rate

L6_40_MEMORY_STORE_SCHEMA = "tiangong.l6_40.memory_store_bridge.v1"
SENSITIVE_TOKENS = ("api_key", "secret", "token", "password", "credential", "authorization", "bearer ", "sk-")


def _safe_summary(value: Any, *, limit: int = 700) -> str:
    text = redact_text(str(value or ""))
    lowered = text.lower()
    if any(token in lowered for token in SENSITIVE_TOKENS):
        text = redact_text(text)
        for token in SENSITIVE_TOKENS:
            text = text.replace(token, f"{token[:2]}***")
    return text[:limit]


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    schema_version: str = L6_40_MEMORY_STORE_SCHEMA
    memory_level: MemoryLevel | str = MemoryLevel.L1
    memory_category: MemoryCategory | str = MemoryCategory.WORKING
    sanitized_summary: str = ""
    content_digest: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    source_task_ref: str = ""
    source_audit_refs: tuple[str, ...] = field(default_factory=tuple)
    confidence_score: float = 0.5
    importance_score: float = 0.5
    task_relevance_score: float = 0.5
    reuse_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    privacy_risk_score: float = 0.0
    pollution_risk_score: float = 0.0
    conflict_score: float = 0.0
    created_at: float = field(default_factory=time)
    updated_at: float = field(default_factory=time)
    last_accessed_at: float = field(default_factory=time)
    half_life_seconds: float = 6 * 60 * 60
    tombstone_state: str = "none"
    active_recall_suppressed: bool = False
    retention_policy_ref: str = "policy:l6_40_memory_default_retention"
    user_forget_request_ref: str = ""
    public_projection_allowed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.memory_id, str) or not self.memory_id.strip():
            raise ValueError("MemoryRecord.memory_id must be non-empty text")
        object.__setattr__(self, "memory_level", MemoryLevel(self.memory_level))
        object.__setattr__(self, "memory_category", MemoryCategory(self.memory_category))
        object.__setattr__(self, "sanitized_summary", _safe_summary(self.sanitized_summary))
        for field_name in (
            "confidence_score",
            "importance_score",
            "task_relevance_score",
            "privacy_risk_score",
            "pollution_risk_score",
            "conflict_score",
        ):
            ensure_score(getattr(self, field_name), f"MemoryRecord.{field_name}")
        for field_name in ("reuse_count", "success_count", "failure_count"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"MemoryRecord.{field_name} must be non-negative int")
        for field_name in ("created_at", "updated_at", "last_accessed_at", "half_life_seconds"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"MemoryRecord.{field_name} must be numeric")
        if self.half_life_seconds <= 0:
            raise ValueError("MemoryRecord.half_life_seconds must be positive")
        for field_name in ("evidence_refs", "source_audit_refs"):
            if not isinstance(getattr(self, field_name), tuple):
                raise ValueError(f"MemoryRecord.{field_name} must be tuple")
        for field_name in ("active_recall_suppressed", "public_projection_allowed"):
            ensure_bool(getattr(self, field_name), f"MemoryRecord.{field_name}")
        if self.public_projection_allowed and self.privacy_risk_score >= 0.30:
            raise ValueError("MemoryRecord.public_projection_allowed cannot be true for private-risk memory")
        if not self.content_digest:
            object.__setattr__(self, "content_digest", _digest({"summary": self.sanitized_summary, "evidence_refs": self.evidence_refs}))

    @property
    def observed_success_rate(self) -> float:
        return success_rate(self.success_count, self.failure_count)

    @property
    def runtime_level_weight(self) -> float:
        return level_weight(self.memory_level)

    def public_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "schema_version": self.schema_version,
            "memory_level": self.memory_level.value,
            "memory_category": self.memory_category.value,
            "sanitized_summary": self.sanitized_summary,
            "content_digest": self.content_digest,
            "evidence_refs": list(self.evidence_refs),
            "source_task_ref": self.source_task_ref,
            "source_audit_refs": list(self.source_audit_refs),
            "confidence_score": self.confidence_score,
            "importance_score": self.importance_score,
            "task_relevance_score": self.task_relevance_score,
            "reuse_count": self.reuse_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "privacy_risk_score": self.privacy_risk_score,
            "pollution_risk_score": self.pollution_risk_score,
            "conflict_score": self.conflict_score,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_accessed_at": self.last_accessed_at,
            "half_life_seconds": self.half_life_seconds,
            "tombstone_state": self.tombstone_state,
            "active_recall_suppressed": self.active_recall_suppressed,
            "retention_policy_ref": self.retention_policy_ref,
            "user_forget_request_ref": self.user_forget_request_ref,
            "public_projection_allowed": self.public_projection_allowed,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MemoryRecord":
        data = dict(payload)
        for key in ("evidence_refs", "source_audit_refs"):
            data[key] = tuple(data.get(key) or ())
        return cls(**data)

    def with_updates(self, **updates: Any) -> "MemoryRecord":
        data = self.public_dict()
        data.update(updates)
        data["evidence_refs"] = tuple(data.get("evidence_refs") or ())
        data["source_audit_refs"] = tuple(data.get("source_audit_refs") or ())
        data["updated_at"] = float(updates.get("updated_at", data.get("updated_at", time())))
        return MemoryRecord.from_dict(data)


@dataclass(frozen=True)
class MemoryStoreEvent:
    event_id: str
    event_type: str
    created_at: float
    memory_id: str
    payload: dict[str, Any]
    event_hash: str = ""

    def public_dict(self) -> dict[str, Any]:
        base = {
            "schema": L6_40_MEMORY_STORE_SCHEMA,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "created_at": self.created_at,
            "memory_id": self.memory_id,
            "payload": self.payload,
        }
        base["event_hash"] = self.event_hash or _digest(base)
        return base


class MemoryStoreBridge:
    """Append-only JSONL bridge; reconstructs current records by replaying events."""

    def __init__(self, store_path: str | Path) -> None:
        self.store_path = Path(store_path).expanduser().resolve()
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_path.exists():
            self.store_path.write_text("", encoding="utf-8")

    def _append_event(self, event_type: str, memory_id: str, payload: dict[str, Any]) -> MemoryStoreEvent:
        event = MemoryStoreEvent(
            event_id=f"memevt_{uuid4().hex[:16]}",
            event_type=event_type,
            created_at=time(),
            memory_id=memory_id,
            payload=payload,
        )
        public = event.public_dict()
        with self.store_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(public, ensure_ascii=False, sort_keys=True) + "\n")
        return MemoryStoreEvent(
            event_id=public["event_id"],
            event_type=public["event_type"],
            created_at=public["created_at"],
            memory_id=public["memory_id"],
            payload=dict(public["payload"]),
            event_hash=public["event_hash"],
        )

    def add_candidate(self, record: MemoryRecord) -> MemoryStoreEvent:
        if record.tombstone_state != "none" or record.active_recall_suppressed:
            raise ValueError("cannot add already tombstoned or suppressed memory as active candidate")
        return self._append_event("candidate_added", record.memory_id, {"record": record.public_dict()})

    def mark_tombstone(self, memory_id: str, *, reason_ref: str = "review:l6_40_tombstone") -> MemoryStoreEvent:
        if not memory_id:
            raise ValueError("memory_id is required")
        return self._append_event("tombstone_marked", memory_id, {"tombstone_state": "tombstoned", "reason_ref": reason_ref})

    def suppress_active_recall(self, memory_id: str, *, reason_ref: str = "review:l6_40_active_recall_suppression") -> MemoryStoreEvent:
        if not memory_id:
            raise ValueError("memory_id is required")
        return self._append_event("active_recall_suppressed", memory_id, {"active_recall_suppressed": True, "reason_ref": reason_ref})

    def record_use_feedback(self, memory_id: str, *, used_successfully: bool, reason_ref: str = "evidence:l6_40_memory_use_feedback") -> MemoryStoreEvent:
        ensure_bool(used_successfully, "MemoryStoreBridge.used_successfully")
        return self._append_event("use_feedback_recorded", memory_id, {"used_successfully": used_successfully, "reason_ref": reason_ref})

    def read_events(self) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        if not self.store_path.exists():
            return events
        for line in self.store_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            expected = _digest({k: v for k, v in event.items() if k != "event_hash"})
            if event.get("event_hash") != expected:
                raise ValueError(f"MemoryStore event hash mismatch: {event.get('event_id')}")
            events.append(event)
        return events

    def replay_records(self) -> dict[str, MemoryRecord]:
        records: dict[str, MemoryRecord] = {}
        for event in self.read_events():
            memory_id = str(event.get("memory_id") or "")
            payload = dict(event.get("payload") or {})
            kind = event.get("event_type")
            if kind == "candidate_added":
                records[memory_id] = MemoryRecord.from_dict(payload["record"])
            elif kind == "tombstone_marked" and memory_id in records:
                event_time = float(event.get("created_at") or records[memory_id].updated_at)
                records[memory_id] = records[memory_id].with_updates(tombstone_state="tombstoned", updated_at=event_time)
            elif kind == "active_recall_suppressed" and memory_id in records:
                event_time = float(event.get("created_at") or records[memory_id].updated_at)
                records[memory_id] = records[memory_id].with_updates(active_recall_suppressed=True, updated_at=event_time)
            elif kind == "use_feedback_recorded" and memory_id in records:
                current = records[memory_id]
                event_time = float(event.get("created_at") or current.updated_at)
                success_delta = 1 if payload.get("used_successfully") else 0
                failure_delta = 0 if payload.get("used_successfully") else 1
                records[memory_id] = current.with_updates(
                    reuse_count=current.reuse_count + 1,
                    success_count=current.success_count + success_delta,
                    failure_count=current.failure_count + failure_delta,
                    last_accessed_at=event_time,
                    updated_at=event_time,
                )
        return records

    def export_snapshot(self, path: str | Path | None = None) -> dict[str, Any] | Path:
        records = [record.public_dict() for record in self.replay_records().values()]
        payload = {
            "schema": L6_40_MEMORY_STORE_SCHEMA,
            "store_path_digest": _digest(str(self.store_path)),
            "event_count": len(self.read_events()),
            "records": records,
            "summary_only": True,
            "append_only": True,
            "no_raw_memory_body": True,
            "no_physical_delete": True,
        }
        if path is None:
            return payload
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return target

    def active_records(self) -> list[MemoryRecord]:
        return [
            record
            for record in self.replay_records().values()
            if record.tombstone_state == "none" and not record.active_recall_suppressed
        ]

    def age_seconds(self, record: MemoryRecord, *, now: float | None = None) -> float:
        return elapsed_since(record.last_accessed_at, now=now)
