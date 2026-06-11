from __future__ import annotations

"""L6.71.7 streaming render helpers.

The helpers here are intentionally UI-framework neutral. Tkinter can use them
now; a later Tauri/React shell can reuse the same semantics. They optimize
render frequency and transcript size without taking over Runtime execution.
"""

from collections import deque
from dataclasses import dataclass, field
from time import monotonic
from typing import Deque, Iterable, List, Optional

from .agent_ui_events import AgentUiEvent
from .runtime_snapshot import ChatMessage, CHAT_MESSAGE_DISPLAY_LIMIT, safe_chat_text, safe_text


STREAM_RENDER_CONTRACT_VERSION = "tiangong.l6_54.stream_smooth_render.v1"

STREAM_ACTIVE_MESSAGE_LIMIT = min(24000, CHAT_MESSAGE_DISPLAY_LIMIT)
STREAM_FINAL_MESSAGE_LIMIT = CHAT_MESSAGE_DISPLAY_LIMIT



@dataclass
class EventBuffer:
    max_events: int = 512
    _events: Deque[AgentUiEvent] = field(default_factory=deque)

    def push(self, event: AgentUiEvent) -> None:
        self._events.append(event)
        while len(self._events) > self.max_events:
            self._events.popleft()

    def drain(self, limit: Optional[int] = None) -> List[AgentUiEvent]:
        if limit is None or limit < 0:
            limit = len(self._events)
        drained: List[AgentUiEvent] = []
        for _ in range(min(limit, len(self._events))):
            drained.append(self._events.popleft())
        return drained

    def snapshot(self) -> List[AgentUiEvent]:
        return list(self._events)

    def __len__(self) -> int:
        return len(self._events)


@dataclass
class DeltaMerger:
    flush_interval_ms: int = 45
    max_chars: int = 1200
    _parts: List[str] = field(default_factory=list)
    _last_flush_at: float = field(default_factory=monotonic)

    def push(self, text: str) -> None:
        clean = safe_chat_text(text, self.max_chars)
        if clean:
            self._parts.append(clean)

    @property
    def pending_chars(self) -> int:
        return sum(len(part) for part in self._parts)

    def should_flush(self, *, force: bool = False) -> bool:
        if not self._parts:
            return False
        if force:
            return True
        if self.pending_chars >= self.max_chars:
            return True
        return (monotonic() - self._last_flush_at) * 1000 >= self.flush_interval_ms

    def flush(self, *, force: bool = False) -> str:
        if not self.should_flush(force=force):
            return ""
        text = "".join(self._parts)
        self._parts.clear()
        self._last_flush_at = monotonic()
        return safe_chat_text(text, max(self.max_chars, len(text) + 1))


@dataclass
class VirtualTranscript:
    max_visible_messages: int = 80
    _messages: List[ChatMessage] = field(default_factory=list)
    hidden_message_count: int = 0
    _active_assistant_index: Optional[int] = None

    def load(self, messages: Iterable[ChatMessage]) -> None:
        self._messages = list(messages)
        self._active_assistant_index = None
        self._trim()

    def append_message(self, message: ChatMessage) -> None:
        self._messages.append(message)
        if message.role == "assistant":
            self._active_assistant_index = len(self._messages) - 1
        else:
            self._active_assistant_index = None
        self._trim()

    def append_assistant_delta(self, text: str, *, label: str = "临渊者", time: str = "流式") -> None:
        clean = safe_chat_text(text, STREAM_ACTIVE_MESSAGE_LIMIT)
        if not clean:
            return
        idx = self._active_assistant_index
        if idx is None or idx >= len(self._messages) or self._messages[idx].role != "assistant":
            self._messages.append(ChatMessage("assistant", label, time, clean))
            self._active_assistant_index = len(self._messages) - 1
        else:
            self._messages[idx].text = safe_chat_text(self._messages[idx].text + clean, STREAM_ACTIVE_MESSAGE_LIMIT)
        self._trim()

    def finalize_assistant(self, text: str, *, label: str = "临渊者", time: str = "完成") -> None:
        clean = safe_chat_text(text, STREAM_FINAL_MESSAGE_LIMIT)
        idx = self._active_assistant_index
        if clean and idx is not None and 0 <= idx < len(self._messages) and self._messages[idx].role == "assistant":
            current = safe_chat_text(self._messages[idx].text, STREAM_FINAL_MESSAGE_LIMIT)
            if clean == current or clean.endswith(current):
                self._messages[idx].text = clean
                self._messages[idx].time = time
            elif current.endswith(clean):
                self._messages[idx].time = time
            elif self._messages[idx].time in {"流式", "streaming", "输出中"}:
                # Runtime 的 assistant_final 是最终可见交付。若增量片段与 final
                # 不是前后缀关系，仍应替换正在流式中的临时消息，避免用户看到
                # “半截输出 + 完整输出”两条重复气泡。
                self._messages[idx].text = clean
                self._messages[idx].time = time
            else:
                self._messages.append(ChatMessage("assistant", label, time, clean))
        elif clean:
            self._messages.append(ChatMessage("assistant", label, time, clean))
        self._active_assistant_index = None
        self._trim()

    def visible_messages(self) -> List[ChatMessage]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()
        self.hidden_message_count = 0
        self._active_assistant_index = None

    @property
    def visible_message_count(self) -> int:
        return len(self._messages)

    def _trim(self) -> None:
        overflow = max(0, len(self._messages) - self.max_visible_messages)
        if overflow:
            self._messages = self._messages[overflow:]
            self.hidden_message_count += overflow
            if self._active_assistant_index is not None:
                self._active_assistant_index = max(0, self._active_assistant_index - overflow)


@dataclass
class RenderScheduler:
    min_interval_ms: int = 45
    _last_render_at: float = field(default_factory=lambda: 0.0)

    def should_render(self, *, force: bool = False) -> bool:
        if force:
            self._last_render_at = monotonic()
            return True
        now = monotonic()
        if (now - self._last_render_at) * 1000 >= self.min_interval_ms:
            self._last_render_at = now
            return True
        return False


def streaming_policy() -> dict:
    return {
        "contract_version": STREAM_RENDER_CONTRACT_VERSION,
        "render_strategy": "event_buffer_delta_merge_virtual_transcript",
        "recommended_flush_interval_ms": 45,
        "max_visible_messages_default": 80,
        "stream_visual_states": ["thinking", "streaming", "reconnecting", "completed", "error", "interrupted"],
        "thinking_indicator": "ui_only_non_executing",
        "frontend_execution_permission": "none",
    }
