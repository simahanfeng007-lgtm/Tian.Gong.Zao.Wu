"""L5 phase 2 manifest quality gate.

The gate validates in-memory manifest declarations and returns a validation
report. It does not register plugins, mutate state, issue permits, write audit
stores, execute tests, or contact external systems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_text, ensure_schema_version
from .audit_declaration import PluginAuditDeclaration
from .capability_token_declaration import PluginCapabilityTokenDeclaration
from .compatibility_declaration import PluginCompatibilityDeclaration
from .credential_declaration import PluginCredentialDeclaration
from .data_governance_declaration import PluginDataGovernanceDeclaration
from .entry_reference import PluginEntryReference
from .manifest_hash import calculate_manifest_digest
from .manifest_schema import PluginManifestSchema
from .manifest_validation import PluginManifestValidationIssue, PluginManifestValidationReport
from .mount_surface_declaration import PluginMountSurfaceDeclaration
from .permission_declaration import PluginPermissionDeclaration
from .phase2_common import ALLOWED_PLUGIN_KINDS, SEVERITY_P0, SEVERITY_P1, ensure_no_executable_reference, suspicious_credential_value_paths
from .resource_declaration import PluginResourceDeclaration
from .rollback_declaration import PluginRollbackDeclaration
from .signature_reference import PluginSignatureReference
from .source_trust import PluginSourceTrustReference
from .trust_boundary_declaration import PluginTrustBoundaryDeclaration
from .version_declaration import PluginVersionDeclaration


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_tuple(value: Any) -> bool:
    return isinstance(value, (tuple, list)) and bool(value)


def _issue(code: str, field_path: str, message: str, severity: str = SEVERITY_P1) -> PluginManifestValidationIssue:
    return PluginManifestValidationIssue(
        issue_code=code,
        severity=severity,
        field_path=field_path,
        message=message,
        blocking=severity in (SEVERITY_P0, SEVERITY_P1),
        evidence_ref=f"evidence:{code.lower()}",
    )


@dataclass(frozen=True, slots=True)
class PluginManifestQualityGate:
    gate_ref: str
    schema: PluginManifestSchema
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.gate_ref, "PluginManifestQualityGate.gate_ref")
        if not isinstance(self.schema, PluginManifestSchema):
            raise ValueError("PluginManifestQualityGate.schema must be PluginManifestSchema")
        ensure_schema_version(self.schema_version, "PluginManifestQualityGate.schema_version")

    def evaluate(self, manifest: Any) -> PluginManifestValidationReport:
        issues: list[PluginManifestValidationIssue] = []
        manifest_ref = getattr(manifest, "plugin_id", "manifest:unknown") or "manifest:unknown"

        def require_text(attr: str, field_path: str | None = None) -> None:
            if not _has_text(getattr(manifest, attr, "")):
                issues.append(_issue(f"MISSING_{attr.upper()}", field_path or attr, f"{attr} is required"))

        def require_tuple(attr: str, field_path: str | None = None) -> None:
            if not _has_tuple(getattr(manifest, attr, tuple())):
                issues.append(_issue(f"MISSING_{attr.upper()}", field_path or attr, f"{attr} is required"))

        def require_instance(attr: str, expected_type: type[Any]) -> Any:
            value = getattr(manifest, attr, None)
            if not isinstance(value, expected_type):
                issues.append(_issue(f"MISSING_{attr.upper()}", attr, f"{attr} must be {expected_type.__name__}"))
                return None
            return value

        for attr in (
            "plugin_id",
            "schema_version",
            "manifest_version",
            "package_ref",
            "created_at_ref",
            "producer_ref",
            "boundary_baseline_ref",
            "no_live_external_action_guarantee_ref",
            "no_l6_implementation_guarantee_ref",
            "no_lower_layer_mutation_guarantee_ref",
            "no_legacy_runtime_guarantee_ref",
            "actor_ref",
            "scope_ref",
            "trace_ref",
            "policy_ref",
            "approval_ref",
            "accountability_ref",
            "tamper_evidence_ref",
        ):
            require_text(attr)

        if not (_has_text(getattr(manifest, "plugin_name", "")) or _has_text(getattr(manifest, "name", ""))):
            issues.append(_issue("MISSING_PLUGIN_NAME", "plugin_name", "plugin_name is required"))
        plugin_kind = getattr(manifest, "plugin_kind", "") or getattr(manifest, "kind", "")
        if plugin_kind not in ALLOWED_PLUGIN_KINDS:
            issues.append(_issue("INVALID_PLUGIN_KIND", "plugin_kind", "plugin_kind must be in the allowed set"))

        for version_attr in ("schema_version", "manifest_version"):
            value = getattr(manifest, version_attr, "")
            if not isinstance(value, str) or len(value.split(".")) < 2:
                issues.append(_issue(f"INVALID_{version_attr.upper()}", version_attr, f"{version_attr} must be dotted version text"))

        entry_ref = require_instance("entry_ref", PluginEntryReference)
        if entry_ref is not None:
            try:
                ensure_no_executable_reference(entry_ref.entry_ref, "entry_ref.entry_ref")
            except ValueError:
                issues.append(_issue("EXECUTABLE_ENTRY_REF", "entry_ref", "entry_ref must be a non-executable logical reference", SEVERITY_P0))

        for attr, expected in (
            ("permission_decl", PluginPermissionDeclaration),
            ("resource_decl", PluginResourceDeclaration),
            ("credential_decl", PluginCredentialDeclaration),
            ("data_governance_decl", PluginDataGovernanceDeclaration),
            ("audit_decl", PluginAuditDeclaration),
            ("version_decl", PluginVersionDeclaration),
            ("rollback_decl", PluginRollbackDeclaration),
            ("compatibility_decl", PluginCompatibilityDeclaration),
            ("capability_token_decl", PluginCapabilityTokenDeclaration),
            ("trust_boundary_decl", PluginTrustBoundaryDeclaration),
            ("source_trust_ref", PluginSourceTrustReference),
            ("signature_ref", PluginSignatureReference),
        ):
            require_instance(attr, expected)

        mount_surfaces = getattr(manifest, "mount_surfaces", tuple())
        if not isinstance(mount_surfaces, tuple) or not mount_surfaces:
            issues.append(_issue("MISSING_MOUNT_SURFACES", "mount_surfaces", "mount_surfaces are required"))
        else:
            for index, surface in enumerate(mount_surfaces):
                if not isinstance(surface, PluginMountSurfaceDeclaration):
                    issues.append(_issue("INVALID_MOUNT_SURFACE", f"mount_surfaces[{index}]", "mount_surfaces must contain declarations"))

        for attr in ("handoff_evidence_refs", "provenance_refs", "lifecycle_event_refs", "consent_refs", "purpose_refs", "data_lifecycle_refs"):
            require_tuple(attr)

        resource_decl = getattr(manifest, "resource_decl", None)
        if isinstance(resource_decl, PluginResourceDeclaration):
            for attr in ("cost_budget_ref", "rate_limit_ref", "quota_ref", "budget_owner_ref", "run_budget_scope_ref", "goal_budget_scope_ref", "actor_budget_scope_ref"):
                if not _has_text(getattr(resource_decl, attr, "")):
                    issues.append(_issue(f"RESOURCE_MISSING_{attr.upper()}", f"resource_decl.{attr}", f"resource_decl.{attr} is required"))
            if not resource_decl.high_permission_does_not_bypass_budget:
                issues.append(_issue("RESOURCE_BUDGET_BYPASS", "resource_decl.high_permission_does_not_bypass_budget", "high permission must not bypass budgets", SEVERITY_P0))

        credential_decl = getattr(manifest, "credential_decl", None)
        if isinstance(credential_decl, PluginCredentialDeclaration):
            if not _has_tuple(credential_decl.credential_handle_refs):
                issues.append(_issue("CREDENTIAL_MISSING_HANDLE_REFS", "credential_decl.credential_handle_refs", "credential handles are required"))
            if not _has_tuple(credential_decl.credential_purpose_refs):
                issues.append(_issue("CREDENTIAL_MISSING_PURPOSE_REFS", "credential_decl.credential_purpose_refs", "credential purposes are required"))
            if not _has_text(credential_decl.credential_lease_ref):
                issues.append(_issue("CREDENTIAL_MISSING_LEASE", "credential_decl.credential_lease_ref", "credential lease is required"))
            if not _has_text(credential_decl.credential_revocation_ref):
                issues.append(_issue("CREDENTIAL_MISSING_REVOCATION", "credential_decl.credential_revocation_ref", "credential revocation is required"))
            if not credential_decl.value_absent_required or not credential_decl.redacted_required:
                issues.append(_issue("CREDENTIAL_VALUE_NOT_ABSENT_OR_REDACTED", "credential_decl", "credential values must be absent and redacted", SEVERITY_P0))

        data_governance_decl = getattr(manifest, "data_governance_decl", None)
        if isinstance(data_governance_decl, PluginDataGovernanceDeclaration):
            for attr in ("consent_refs", "purpose_refs", "data_lifecycle_refs"):
                if not _has_tuple(getattr(data_governance_decl, attr)):
                    issues.append(_issue(f"DATA_GOVERNANCE_MISSING_{attr.upper()}", f"data_governance_decl.{attr}", f"data_governance_decl.{attr} is required"))

        capability_token_decl = getattr(manifest, "capability_token_decl", None)
        if isinstance(capability_token_decl, PluginCapabilityTokenDeclaration):
            if not _has_tuple(capability_token_decl.token_scope_refs):
                issues.append(_issue("CAPABILITY_TOKEN_MISSING_SCOPE", "capability_token_decl.token_scope_refs", "token scope is required"))
            if not _has_text(capability_token_decl.lease_ref):
                issues.append(_issue("CAPABILITY_TOKEN_MISSING_LEASE", "capability_token_decl.lease_ref", "token lease is required"))
            if not (_has_text(capability_token_decl.expires_at_ref) or _has_text(capability_token_decl.expiry_ref)):
                issues.append(_issue("CAPABILITY_TOKEN_MISSING_EXPIRY", "capability_token_decl.expiry_ref", "token expiry is required"))
            if not _has_text(capability_token_decl.revocation_check_ref):
                issues.append(_issue("CAPABILITY_TOKEN_MISSING_REVOCATION", "capability_token_decl.revocation_check_ref", "token revocation check is required"))

        trust_boundary_decl = getattr(manifest, "trust_boundary_decl", None)
        if isinstance(trust_boundary_decl, PluginTrustBoundaryDeclaration):
            for attr in ("host_boundary_ref", "plugin_boundary_ref"):
                if not _has_text(getattr(trust_boundary_decl, attr)):
                    issues.append(_issue(f"TRUST_BOUNDARY_MISSING_{attr.upper()}", f"trust_boundary_decl.{attr}", f"trust_boundary_decl.{attr} is required"))
            if not _has_tuple(trust_boundary_decl.data_boundary_refs):
                issues.append(_issue("TRUST_BOUNDARY_MISSING_DATA_BOUNDARY", "trust_boundary_decl.data_boundary_refs", "data boundary refs are required"))
            if isinstance(credential_decl, PluginCredentialDeclaration) and not _has_tuple(trust_boundary_decl.credential_boundary_refs):
                issues.append(_issue("TRUST_BOUNDARY_MISSING_CREDENTIAL_BOUNDARY", "trust_boundary_decl.credential_boundary_refs", "credential boundary refs are required"))
            if isinstance(data_governance_decl, PluginDataGovernanceDeclaration) and _has_text(data_governance_decl.external_disclosure_policy_ref) and not _has_tuple(trust_boundary_decl.external_disclosure_boundary_refs):
                issues.append(_issue("TRUST_BOUNDARY_MISSING_EXTERNAL_DISCLOSURE_BOUNDARY", "trust_boundary_decl.external_disclosure_boundary_refs", "external disclosure boundary refs are required"))
            if _has_tuple(mount_surfaces) and not _has_tuple(trust_boundary_decl.tool_boundary_refs):
                issues.append(_issue("TRUST_BOUNDARY_MISSING_TOOL_BOUNDARY", "trust_boundary_decl.tool_boundary_refs", "tool boundary refs are required for mount surfaces"))
            if isinstance(resource_decl, PluginResourceDeclaration) and _has_text(resource_decl.network_budget_ref) and not _has_tuple(trust_boundary_decl.network_boundary_refs):
                issues.append(_issue("TRUST_BOUNDARY_MISSING_NETWORK_BOUNDARY", "trust_boundary_decl.network_boundary_refs", "network boundary refs are required"))

        audit_decl = getattr(manifest, "audit_decl", None)
        if isinstance(audit_decl, PluginAuditDeclaration):
            for attr in ("actor_required", "scope_required", "accountability_required", "tamper_evidence_required", "evidence_required", "trace_required"):
                if not bool(getattr(audit_decl, attr)):
                    issues.append(_issue(f"AUDIT_MISSING_{attr.upper()}", f"audit_decl.{attr}", f"audit_decl.{attr} must be true"))

        if suspicious_credential_value_paths(manifest, "manifest"):
            issues.append(_issue("SUSPECTED_PLAIN_CREDENTIAL_VALUE", "manifest", "manifest contains suspected plain credential values", SEVERITY_P0))

        manifest_hash = getattr(manifest, "manifest_hash", "") or getattr(manifest, "manifest_digest", "")
        if not _has_text(manifest_hash):
            issues.append(_issue("MISSING_MANIFEST_HASH", "manifest_hash", "manifest hash is required"))
        else:
            calculated = calculate_manifest_digest(manifest)
            if manifest_hash != calculated:
                issues.append(_issue("MANIFEST_HASH_MISMATCH", "manifest_hash", "manifest hash must match canonical payload digest"))

        summary = "passed" if not any(issue.blocking for issue in issues) else "blocked"
        return PluginManifestValidationReport(
            report_ref=f"manifest_validation:{manifest_ref}",
            manifest_ref=manifest_ref,
            issues=tuple(issues),
            observed_summary=summary,
        )
