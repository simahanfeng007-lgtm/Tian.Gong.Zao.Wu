"""Session 回填桥。"""

from __future__ import annotations

from typing import Any

from .tool_result import ToolResult


def results_to_session_message(results: list[ToolResult]) -> dict[str, Any]:
    lines = []
    for result in results:
        lines.append(f"[{result.status.value}] {result.tool_name}: {result.output_summary}")
    return {"role": "assistant", "content": "\n".join(lines)}
