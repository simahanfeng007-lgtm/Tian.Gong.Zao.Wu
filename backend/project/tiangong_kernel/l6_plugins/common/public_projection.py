"""L6 public projection contract.

Public projection is the minimum-disclosure view used for UI, handoff, and
freeze summaries. It excludes raw prompts, credentials, endpoints, schemas,
callables, paths, database locators, and complete internal plans.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L6_COMMON_SCHEMA_VERSION, ensure_no_live_or_sensitive_text, ensure_ref_items, ensure_ref_or_summary_items, ensure_ref_text, ensure_schema_version, stable_primitive


@dataclass(frozen=True, slots=True)
class L6PublicProjection:
    projection_ref: str = "public:l6_public_projection"
    plugin_ref: str = "l6:plugin_ref"
    status_summary: str = "declared_summary_only"
    risk_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_risk_summary_ref",))
    health_summary_refs: tuple[str, ...] = field(default_factory=tuple)
    budget_summary_refs: tuple[str, ...] = field(default_factory=tuple)
    audit_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("audit:l6_public_audit_summary_ref",))
    state_projection_summary_refs: tuple[str, ...] = field(default_factory=tuple)
    event_summary_refs: tuple[str, ...] = field(default_factory=tuple)
    test_summary_refs: tuple[str, ...] = field(default_factory=tuple)
    readiness_summary_refs: tuple[str, ...] = field(default_factory=tuple)
    redacted_evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    disclosure_policy_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_minimum_public_disclosure",))
    contains_raw_credential: bool = False
    contains_provider_locator: bool = False
    contains_raw_prompt: bool = False
    contains_tool_schema: bool = False
    contains_function_schema: bool = False
    contains_external_endpoint: bool = False
    contains_real_path: bool = False
    contains_complete_internal_plan: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.projection_ref, "L6PublicProjection.projection_ref")
        ensure_ref_text(self.plugin_ref, "L6PublicProjection.plugin_ref")
        ensure_no_live_or_sensitive_text(self.status_summary, "L6PublicProjection.status_summary")
        for field_name in (
            "risk_summary_refs", "health_summary_refs", "budget_summary_refs", "audit_summary_refs",
            "state_projection_summary_refs", "event_summary_refs", "test_summary_refs", "readiness_summary_refs",
            "redacted_evidence_refs", "disclosure_policy_refs",
        ):
            ensure_ref_or_summary_items(getattr(self, field_name), f"L6PublicProjection.{field_name}")
        if any((self.contains_raw_credential, self.contains_provider_locator, self.contains_raw_prompt, self.contains_tool_schema, self.contains_function_schema, self.contains_external_endpoint, self.contains_real_path, self.contains_complete_internal_plan)):
            raise ValueError("L6 public projection contains forbidden disclosure")
        ensure_schema_version(self.schema_version)

    def to_public_primitive(self) -> dict[str, object]:
        return stable_primitive(self)
