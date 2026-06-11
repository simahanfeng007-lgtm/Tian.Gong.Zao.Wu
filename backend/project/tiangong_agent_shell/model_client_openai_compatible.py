"""OpenAI-compatible 模型客户端兼容入口。

L6.72.58 起真实实现迁移到 providers/openai_compatible_adapter.py；保留本文件
是为了不破坏旧 import 路径。
"""

from __future__ import annotations

from .providers.openai_compatible_adapter import OpenAICompatibleAdapter


class OpenAICompatibleModelClient(OpenAICompatibleAdapter):
    provider = "openai_compatible"
