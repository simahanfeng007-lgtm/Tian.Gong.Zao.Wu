"""Deterministic L5 phase 2 manifest digest shells."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_digest, ensure_ref_text, ensure_schema_version, stable_digest
from .phase2_common import to_phase2_primitive

CANONICAL_MANIFEST_HASH_EXCLUDED_FIELDS = (
    "manifest_hash",
    "manifest_digest",
    "signature_ref",
    "source_trust_ref",
    "validation_time",
    "generated_at",
    "report_path",
    "temporary_path",
    "recorded_at",
)


def canonical_manifest_payload(value: Any, excluded_fields: tuple[str, ...] = CANONICAL_MANIFEST_HASH_EXCLUDED_FIELDS) -> Any:
    primitive = to_phase2_primitive(value)
    excluded = set(excluded_fields)

    def scrub(node: Any) -> Any:
        if isinstance(node, dict):
            return {key: scrub(item) for key, item in sorted(node.items()) if key not in excluded}
        if isinstance(node, list):
            return [scrub(item) for item in node]
        return node

    return scrub(primitive)


def calculate_manifest_digest(value: Any) -> str:
    return stable_digest(canonical_manifest_payload(value))


@dataclass(frozen=True, slots=True)
class PluginManifestDigest:
    digest_ref: str
    digest_value: str
    algorithm: str = "sha256"
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.digest_ref, "PluginManifestDigest.digest_ref")
        ensure_digest(self.digest_value, "PluginManifestDigest.digest_value", required=True)
        ensure_ref_text(self.algorithm, "PluginManifestDigest.algorithm")
        ensure_schema_version(self.schema_version, "PluginManifestDigest.schema_version")


@dataclass(frozen=True, slots=True)
class PluginManifestHash:
    hash_ref: str
    manifest_digest: PluginManifestDigest
    canonical_payload_digest: str
    excluded_fields: tuple[str, ...] = CANONICAL_MANIFEST_HASH_EXCLUDED_FIELDS
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.hash_ref, "PluginManifestHash.hash_ref")
        if not isinstance(self.manifest_digest, PluginManifestDigest):
            raise ValueError("PluginManifestHash.manifest_digest must be PluginManifestDigest")
        ensure_digest(self.canonical_payload_digest, "PluginManifestHash.canonical_payload_digest", required=True)
        ensure_schema_version(self.schema_version, "PluginManifestHash.schema_version")


def build_manifest_hash(hash_ref: str, manifest: Any) -> PluginManifestHash:
    digest_value = calculate_manifest_digest(manifest)
    return PluginManifestHash(
        hash_ref=hash_ref,
        manifest_digest=PluginManifestDigest(digest_ref=f"{hash_ref}:digest", digest_value=digest_value),
        canonical_payload_digest=digest_value,
    )
