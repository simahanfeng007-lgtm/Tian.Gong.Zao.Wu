"""PromptBuilder 兼容层。

L6.72.11 后，散落 prompt 拼接收束到 prompt_compiler.py。本模块只保留旧入口
以兼容 SessionState 和历史调用点，不再自行决定桌面/CLI/Soul/权限文本。
"""

from __future__ import annotations

from typing import Any

from .prompt_compiler import build_prompt_context, compile_prompt


def build_system_prompt(config: Any | None = None, **kwargs: Any) -> str:
    return compile_prompt(build_prompt_context(config, **kwargs)).system_prompt
