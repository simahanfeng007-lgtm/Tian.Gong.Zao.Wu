"""CLI 会话状态。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from .config_loader import ModelConfig
from .prompt_builder import build_system_prompt


@dataclass
class SessionState:
    config: ModelConfig
    session_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    messages: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def create(cls, config: ModelConfig) -> "SessionState":
        session = cls(config=config)
        session.messages.append({"role": "system", "content": build_system_prompt(config)})
        return session

    def set_system_prompt(self, content: str) -> None:
        """刷新 system prompt，不清空当前会话历史。"""
        clean = str(content or "").replace("\x00", "").strip()
        if not clean:
            return
        dialog = [message for message in self.messages if message.get("role") != "system"]
        self.messages = [{"role": "system", "content": clean}] + dialog

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def reset(self) -> None:
        self.messages = [{"role": "system", "content": build_system_prompt(self.config)}]

    def recent_dialog_messages(self, *, turns: int = 3) -> list[dict[str, str]]:
        """返回最近 N 轮非 system 对话，供 Planner/回退聊天显式续接上下文。"""
        count = max(1, int(turns)) * 2
        return [message for message in self.messages if message.get("role") != "system"][-count:]

    def build_context_hint(self, *, turns: int = 3, max_chars: int = 2400) -> str:
        """压缩最近会话摘要给模型 Planner 使用。

        L6.34 只传安全的最近对话摘录，不做长期记忆写入；作用是让
        ``model_suggest`` 能理解“上面代码 / 上一步结果 / 刚才文件”等引用。
        """
        recent = self.recent_dialog_messages(turns=turns)
        if not recent:
            return ""
        lines = ["CLI 最近会话上下文（仅供计划生成续接上文，不含密钥原文）："]
        for index, message in enumerate(recent, start=1):
            role = str(message.get("role") or "unknown")
            content = str(message.get("content") or "").replace("\x00", "")
            if len(content) > 700:
                content = content[:700] + "…"
            lines.append(f"{index}. {role}: {content}")
        return "\n".join(lines)[:max(200, int(max_chars))]

    @property
    def message_count(self) -> int:
        return len(self.messages)
