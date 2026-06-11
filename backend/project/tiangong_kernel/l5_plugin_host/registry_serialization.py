"""Canonical registry serialization helpers for L5 phase 3.

The helpers operate on in-memory declaration shells only. They never read plugin
packages, inspect directories, touch external systems, or persist registry
state.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from ._common import stable_digest
from .phase2_common import to_phase2_primitive

REGISTRY_DIGEST_EXCLUDED_FIELDS = (
    "snapshot_hash",
    "snapshot_digest",
    "delta_hash",
    "delta_digest",
    "registry_digest",
    "registry_serialization_digest",
    "canonical_record_digest",
    "record_digest",
    "key_digest",
    "generated_at",
    "validation_time",
    "report_path",
    "temporary_path",
    "created_at_text",
    "updated_at_text",
    "created_at_ref",
    "updated_at_ref",
)


def registry_canonical_payload(value: Any, excluded_fields: tuple[str, ...] = REGISTRY_DIGEST_EXCLUDED_FIELDS) -> Any:
    primitive = to_phase2_primitive(value)
    excluded = set(excluded_fields)

    def scrub(node: Any) -> Any:
        if isinstance(node, dict):
            return {key: scrub(item) for key, item in sorted(node.items()) if key not in excluded}
        if isinstance(node, list):
            return [scrub(item) for item in node]
        return node

    return scrub(primitive)


def registry_canonical_digest(value: Any) -> str:
    return stable_digest(registry_canonical_payload(value))


def registry_sort_key(record: Any) -> tuple[str, str, str, str, str]:
    key = getattr(record, "registry_key", None)
    if key is not None:
        return (
            getattr(key, "namespace", ""),
            getattr(key, "plugin_id", ""),
            getattr(key, "plugin_kind", ""),
            getattr(key, "version_ref", "") or getattr(key, "version_text", ""),
            getattr(record, "manifest_hash", ""),
        )
    return (
        getattr(record, "namespace", ""),
        getattr(record, "plugin_id", ""),
        getattr(record, "plugin_kind", ""),
        getattr(record, "version_ref", "") or getattr(record, "version_text", ""),
        getattr(record, "manifest_hash", ""),
    )


def dataclass_to_payload(value: Any) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise TypeError("dataclass_to_payload requires a dataclass instance")
    return {field.name: getattr(value, field.name) for field in fields(value)}


class PluginRegistrySerializationDigest:
    """Namespace-style data helper; contains no runtime registry service."""

    @staticmethod
    def calculate(value: Any) -> str:
        return registry_canonical_digest(value)
