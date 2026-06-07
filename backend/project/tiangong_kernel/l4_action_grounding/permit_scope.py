"""L4 第二阶段许可范围结构。"""

from __future__ import annotations

from dataclasses import dataclass, field

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class PermitScope:
    """许可范围引用结构。

    只表达未来 L5 permit 声明的结构化范围；L4 只做集合包含式结构匹配，不判断是否应该授予。
    """

    action_scope: tuple[str, ...] = field(default_factory=tuple)
    resource_scope: tuple[str, ...] = field(default_factory=tuple)
    environment_scope: tuple[str, ...] = field(default_factory=tuple)
    scope_version: str = "0.1"
    scope_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.action_scope + self.resource_scope + self.environment_scope:
            ensure_short_text(item, "PermitScope item", 128)
        ensure_short_text(self.scope_version, "PermitScope.scope_version", 32)
        ensure_true(self.scope_only, "PermitScope.scope_only")
        ensure_schema_version(self.schema_version, "PermitScope.schema_version")

    def structurally_covers(self, requested_scope: "PermitScope") -> bool:
        """检查 permit scope 是否在结构上覆盖请求 scope，不代表 L4 授权。"""

        return (
            set(requested_scope.action_scope).issubset(set(self.action_scope))
            and set(requested_scope.resource_scope).issubset(set(self.resource_scope))
            and set(requested_scope.environment_scope).issubset(set(self.environment_scope))
        )
