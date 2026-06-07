"""结果摘要裁剪。"""

from __future__ import annotations


def truncate_text(text: str, max_chars: int = 12_000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n...[已截断 {len(text) - max_chars} 字符]"
