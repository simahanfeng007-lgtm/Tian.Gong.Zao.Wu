"""L0 内容引用事实原语，只表达内容、载荷、摘要、编码与安全引用；不保存大内容体、不读写文件。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .identity import RefId


class ContentKind(str, Enum):
    """ContentKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    BINARY = "binary"
    STRUCTURED = "structured"
    UNKNOWN = "unknown"


class PayloadKind(str, Enum):
    """PayloadKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    INLINE_REF = "inline_ref"
    EXTERNAL_REF = "external_ref"
    DIGEST_ONLY = "digest_only"
    REDACTED = "redacted"
    UNKNOWN = "unknown"


class MediaTypeKind(str, Enum):
    """MediaTypeKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    TEXT = "text"
    APPLICATION = "application"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MULTIPART = "multipart"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ContentRef:
    """ContentRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ContentRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContentDigest:
    """ContentDigest 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    algorithm: str
    value: str

    def __post_init__(self) -> None:
        if not self.algorithm:
            raise ValueError("ContentDigest.algorithm cannot be empty")
        if not self.value:
            raise ValueError("ContentDigest.value cannot be empty")


@dataclass(frozen=True, slots=True)
class ContentEncoding:
    """ContentEncoding 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: str = "utf-8"

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("ContentEncoding.value cannot be empty")


@dataclass(frozen=True, slots=True)
class ContentLength:
    """ContentLength 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    bytes_count: int

    def __post_init__(self) -> None:
        if self.bytes_count < 0:
            raise ValueError("ContentLength.bytes_count cannot be negative")


@dataclass(frozen=True, slots=True)
class PayloadRef:
    """PayloadRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: PayloadKind = PayloadKind.UNKNOWN
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PayloadRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PayloadDigest:
    """PayloadDigest 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    algorithm: str
    value: str

    def __post_init__(self) -> None:
        if not self.algorithm:
            raise ValueError("PayloadDigest.algorithm cannot be empty")
        if not self.value:
            raise ValueError("PayloadDigest.value cannot be empty")


@dataclass(frozen=True, slots=True)
class MediaTypeRef:
    """MediaTypeRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: str
    kind: MediaTypeKind = MediaTypeKind.UNKNOWN

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("MediaTypeRef.value cannot be empty")


@dataclass(frozen=True, slots=True)
class ContentDispositionRef:
    """ContentDispositionRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: str = "reference"
    filename_hint: str | None = None

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("ContentDispositionRef.value cannot be empty")


@dataclass(frozen=True, slots=True)
class ContentSafetyRef:
    """ContentSafetyRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    label: str = "unknown"
    policy_ref: RefId | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("ContentSafetyRef.label cannot be empty")
        if not self.schema_version:
            raise ValueError("ContentSafetyRef.schema_version cannot be empty")
