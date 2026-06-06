"""L4 第二阶段许可过期结构。"""

from __future__ import annotations

from dataclasses import dataclass

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class PermitExpiry:
    """许可过期引用结构。

    第二阶段不计算当前时间，只识别 future L5 显式声明的 expiry 与 explicit_expired 标记。
    """

    expires_at_utc: str
    explicit_expired: bool = False
    expiry_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.expires_at_utc, "PermitExpiry.expires_at_utc", 128)
        if not self.expires_at_utc:
            raise ValueError("PermitExpiry.expires_at_utc cannot be empty")
        ensure_true(self.expiry_only, "PermitExpiry.expiry_only")
        ensure_schema_version(self.schema_version, "PermitExpiry.schema_version")

    @property
    def is_expired(self) -> bool:
        """返回 future L5 显式声明的过期状态。"""

        return self.explicit_expired
