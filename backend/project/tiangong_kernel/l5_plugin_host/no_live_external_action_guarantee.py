"""L5 phase 1 guarantee that no live external action is implemented here."""

from __future__ import annotations

from dataclasses import dataclass

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_schema_version, ensure_short_text


@dataclass(frozen=True, slots=True)
class L5NoLiveExternalActionGuarantee:
    guarantee_ref: str
    live_external_action_present: bool = False
    live_adapter_call_present: bool = False
    summary: str = "L5 phase 1 records refs and declarations only."
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.live_external_action_present or self.live_adapter_call_present:
            raise ValueError("L5 phase 1 must not perform live external actions")
        ensure_short_text(self.guarantee_ref, "L5NoLiveExternalActionGuarantee.guarantee_ref", 128)
        ensure_short_text(self.summary, "L5NoLiveExternalActionGuarantee.summary")
        ensure_schema_version(self.schema_version, "L5NoLiveExternalActionGuarantee.schema_version")
