"""L5 phase 1 shared constants and conservative validators.

This module is data-only. It does not discover plugins, load code, touch
external systems, mutate lower layers, or maintain host-global mutable state.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any

L5_PLUGIN_HOST_SCHEMA_VERSION = "0.1"
L5_PLUGIN_HOST_PHASE = "L5.phase1"
MAX_REF_LENGTH = 256
MAX_SUMMARY_LENGTH = 512
MAX_DIGEST_LENGTH = 128

_ALLOWED_MANIFEST_FIELDS = (
    "plugin_id",
    "name",
    "version",
    "kind",
    "declared_entry_ref",
    "declared_permissions",
    "declared_dependencies",
    "declared_lifecycle",
    "declared_boundary_refs",
    "declared_audit_refs",
    "summary",
    "actor_ref",
    "scope_ref",
    "trace_ref",
    "policy_ref",
    "approval_ref",
    "handoff_ref",
    "evidence_refs",
    "provenance_refs",
    "accountability_ref",
    "tamper_evidence_ref",
    "validation_requirement_refs",
    "verification_requirement_refs",
    "evaluation_requirement_refs",
    "regression_requirement_refs",
    "rollback_requirement_refs",
    "health_requirement_refs",
    "manifest_digest",
    "schema_version",
    # L5 phase 2 declarative manifest fields.
    "plugin_name",
    "plugin_kind",
    "manifest_version",
    "entry_ref",
    "package_ref",
    "mount_surfaces",
    "permission_decl",
    "resource_decl",
    "credential_decl",
    "data_governance_decl",
    "audit_decl",
    "version_decl",
    "rollback_decl",
    "compatibility_decl",
    "capability_token_decl",
    "trust_boundary_decl",
    "source_trust_ref",
    "signature_ref",
    "manifest_hash",
    "created_at_ref",
    "created_at_text",
    "producer_ref",
    "boundary_baseline_ref",
    "handoff_evidence_refs",
    "no_live_external_action_guarantee_ref",
    "no_l6_implementation_guarantee_ref",
    "no_lower_layer_mutation_guarantee_ref",
    "no_legacy_runtime_guarantee_ref",
    "lifecycle_event_refs",
    "consent_refs",
    "purpose_refs",
    "data_lifecycle_refs",
    "hot_switch_decl",
)

_ALLOWED_ENTRY_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-:.#")


def stable_primitive(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: stable_primitive(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [stable_primitive(item) for item in value]
    if isinstance(value, list):
        return [stable_primitive(item) for item in value]
    if isinstance(value, frozenset):
        return [stable_primitive(item) for item in sorted(value, key=lambda item: stable_json(stable_primitive(item)))]
    if isinstance(value, set):
        return [stable_primitive(item) for item in sorted(value, key=lambda item: stable_json(stable_primitive(item)))]
    if isinstance(value, dict):
        return {str(key): stable_primitive(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    raise TypeError(f"unsupported L5 phase 1 value: {type(value).__name__}")


def stable_json(value: Any) -> str:
    return json.dumps(stable_primitive(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def stable_digest(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def ensure_bool(value: bool, field_name: str) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")


def ensure_non_empty_text(value: str, field_name: str, limit: int = MAX_REF_LENGTH) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
    ensure_short_text(value, field_name, limit)


def ensure_short_text(value: str, field_name: str, limit: int = MAX_SUMMARY_LENGTH) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be text")
    if len(value) > limit:
        raise ValueError(f"{field_name} exceeds phase 1 length limit")
    if "\x00" in value:
        raise ValueError(f"{field_name} cannot contain null bytes")


def ensure_ref_text(value: str, field_name: str, *, required: bool = True) -> None:
    if required:
        ensure_non_empty_text(value, field_name, MAX_REF_LENGTH)
    elif value == "":
        return
    else:
        ensure_short_text(value, field_name, MAX_REF_LENGTH)
    blocked_fragments = ("\n", "\r", "\x00")
    if any(fragment in value for fragment in blocked_fragments):
        raise ValueError(f"{field_name} must be a compact reference")


def ensure_entry_ref(value: str, field_name: str) -> None:
    ensure_ref_text(value, field_name)
    if "/" in value or "\\" in value or "://" in value:
        raise ValueError(f"{field_name} must be a declaration ref, not an executable path or address")
    if any(char not in _ALLOWED_ENTRY_CHARS for char in value):
        raise ValueError(f"{field_name} contains unsupported entry ref characters")


def ensure_ref_items(items: tuple[str, ...], field_name: str, *, required: bool = False) -> None:
    if not isinstance(items, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if required and not items:
        raise ValueError(f"{field_name} cannot be empty")
    for item in items:
        ensure_ref_text(item, field_name)


def ensure_text_items(items: tuple[str, ...], field_name: str, *, limit: int = MAX_SUMMARY_LENGTH) -> None:
    if not isinstance(items, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    for item in items:
        ensure_short_text(item, field_name, limit)


def ensure_pair_items(items: tuple[tuple[str, str], ...], field_name: str) -> None:
    if not isinstance(items, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    for key, value in items:
        ensure_non_empty_text(key, f"{field_name}.key", 128)
        ensure_short_text(value, f"{field_name}.value", MAX_SUMMARY_LENGTH)


def ensure_digest(value: str, field_name: str, *, required: bool = False) -> None:
    if value == "" and not required:
        return
    ensure_non_empty_text(value, field_name, MAX_DIGEST_LENGTH)
    if len(value) not in (32, 40, 64, 128):
        raise ValueError(f"{field_name} must look like a compact digest")
    if not all(char in "0123456789abcdefABCDEF" for char in value):
        raise ValueError(f"{field_name} must be hex-like")


def ensure_schema_version(value: str, field_name: str = "schema_version") -> None:
    ensure_non_empty_text(value, field_name, 32)


def ensure_allowed_manifest_field_names(names: tuple[str, ...]) -> None:
    unknown = tuple(name for name in names if name not in _ALLOWED_MANIFEST_FIELDS)
    if unknown:
        raise ValueError(f"PluginManifestView contains fields outside phase 1 whitelist: {unknown!r}")


def digest_without(obj: Any, excluded: tuple[str, ...]) -> str:
    if not is_dataclass(obj) or isinstance(obj, type):
        raise TypeError("digest_without requires a dataclass instance")
    payload = {field.name: getattr(obj, field.name) for field in fields(obj) if field.name not in excluded}
    return stable_digest(payload)
