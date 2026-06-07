"""L3 编排稳定序列化辅助函数，委托 L0 序列化原语。"""

from __future__ import annotations

from typing import Any

from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps, to_primitive


def orchestration_to_primitive(value: Any) -> Any:
    """返回 L0 规范化基础结构。"""

    return to_primitive(value)


def orchestration_stable_json(value: Any) -> str:
    """返回稳定 JSON 字符串。"""

    return stable_json_dumps(value)


def orchestration_stable_hash(value: Any) -> str:
    """返回稳定 sha256 摘要。"""

    return stable_hash(value)
