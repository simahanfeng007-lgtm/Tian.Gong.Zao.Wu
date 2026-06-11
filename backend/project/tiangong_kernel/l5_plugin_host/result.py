"""L5 phase 1 result view objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_bool, ensure_schema_version, ensure_text_items
from .error import L5PluginHostError


@dataclass(frozen=True, slots=True)
class L5PluginHostResult:
    ok: bool
    summaries: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[L5PluginHostError, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_bool(self.ok, "L5PluginHostResult.ok")
        ensure_text_items(self.summaries, "L5PluginHostResult.summaries")
        for item in self.errors:
            if not isinstance(item, L5PluginHostError):
                raise ValueError("L5PluginHostResult.errors must contain L5PluginHostError")
        ensure_schema_version(self.schema_version, "L5PluginHostResult.schema_version")
