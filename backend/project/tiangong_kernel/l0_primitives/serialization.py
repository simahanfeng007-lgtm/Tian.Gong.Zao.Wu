"""L0 稳定序列化原语，只做标准库内的确定性值转换与稳定哈希；不访问文件、网络、数据库或注册表。
"""

from __future__ import annotations

from dataclasses import asdict, fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Protocol, TypeVar, runtime_checkable


@runtime_checkable
class StableSerializable(Protocol):
    """稳定序列化协议。

    只要求对象暴露可稳定转成 JSON 基础类型的表示，用于 stable serialization 与 stable hash。
    它不是 schema registry、反射工厂、外部适配器或持久化接口，不读取或写入任何真实资源。
    """

    def to_primitive(self) -> Any:
        """返回可 JSON 表达的稳定基础结构。"""


T = TypeVar("T")


def _sorted_mapping_items(value: dict[Any, Any]) -> list[tuple[str, Any]]:
    return sorted(((str(key), item) for key, item in value.items()), key=lambda pair: pair[0])


def to_primitive(value: Any) -> Any:
    """Convert supported L0 values to deterministic JSON-compatible primitives.

    Supported values: None, bool, int, float, str, Enum, dataclass instances,
    tuple/list/frozenset/set, and dict-like mappings with stringified keys.
    """

    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: to_primitive(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [to_primitive(item) for item in value]
    if isinstance(value, list):
        return [to_primitive(item) for item in value]
    if isinstance(value, frozenset):
        return [to_primitive(item) for item in sorted(value, key=lambda item: stable_json_dumps(to_primitive(item)))]
    if isinstance(value, set):
        return [to_primitive(item) for item in sorted(value, key=lambda item: stable_json_dumps(to_primitive(item)))]
    if isinstance(value, dict):
        return {key: to_primitive(item) for key, item in _sorted_mapping_items(value)}
    if isinstance(value, StableSerializable):
        return to_primitive(value.to_primitive())
    raise TypeError(f"Unsupported L0 serialization value: {type(value).__name__}")


def stable_json_dumps(value: Any) -> str:
    """Return canonical JSON with stable key ordering and compact separators."""

    return json.dumps(
        to_primitive(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def stable_hash(value: Any, *, algorithm: str = "sha256") -> str:
    """Return a deterministic digest over canonical JSON."""

    if algorithm != "sha256":
        raise ValueError("L0 stable_hash only supports sha256 in v0.1")
    payload = stable_json_dumps(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def from_primitive(cls: type[T], value: Any) -> T:
    """Construct a dataclass or enum from primitive data.

    This is intentionally conservative in phase 1. Nested restoration is kept
    shallow to avoid schema registries or upper-layer factories in L0.
    """

    if isinstance(cls, type) and issubclass(cls, Enum):
        return cls(value)  # type: ignore[return-value]
    if is_dataclass(cls):
        if not isinstance(value, dict):
            raise TypeError("Dataclass restoration requires a mapping")
        names = {field.name for field in fields(cls)}
        return cls(**{key: item for key, item in value.items() if key in names})  # type: ignore[misc, return-value]
    return value  # type: ignore[return-value]
