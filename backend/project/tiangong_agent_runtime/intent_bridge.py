"""最小意图桥。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float


class IntentBridge:
    def classify(self, user_message: str) -> IntentResult:
        lowered = user_message.strip().lower()
        if lowered.startswith(("list", "ls", "read", "cat", "write", "compileall", "pytest", "zip")):
            return IntentResult("tool_task", 0.9)
        if lowered.startswith(("列目录", "列出目录", "读取", "写入", "打包")) or "跑 pytest" in lowered or "跑 compileall" in lowered:
            return IntentResult("tool_task", 0.75)
        return IntentResult("chat", 0.5)
