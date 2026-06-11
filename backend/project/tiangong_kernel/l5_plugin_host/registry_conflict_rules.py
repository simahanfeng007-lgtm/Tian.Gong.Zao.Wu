"""L5 phase 3 inert registry conflict pattern catalog and rule markers.

The strings below are inert patterns used to classify declaration text supplied
by tests or caller-provided summaries. This module does not import, execute,
scan files, spawn processes, connect to networks, or persist data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version
from .phase2_common import suspicious_credential_value_paths, to_phase2_primitive

INERT_FORBIDDEN_TOKEN_CATALOG = (
    "importlib.import_module",
    "importlib.util.spec_from_file_location",
    "importlib.machinery",
    "__import__",
    "runpy",
    "pkgutil",
    "exec",
    "eval",
    "subprocess",
    "os.system",
    "os.popen",
    "socket",
    "requests",
    "httpx",
    "urllib",
    "Path.write_text",
    "Path.open",
    "pathlib.Path.open",
    "Path.unlink",
    "Path.rename",
    "Path.replace",
    "shutil.rmtree",
    "shutil.move",
    "shutil.copy",
    "shutil.copytree",
    "tempfile",
    "sqlite3",
    "redis",
    "pymongo",
    "sqlalchemy",
    "multiprocessing",
    "threading",
    "concurrent.futures",
)

LEGACY_RUNTIME_PATTERNS = (
    "AbilityPackage",
    "CapabilityPort",
    "AbilityPackagePort",
)

L6_IMPLEMENTATION_PATTERNS = (
    "MemoryPlugin",
    "LearningPlugin",
    "EvolutionPlugin",
    "RecoveryPlugin",
    "AffectivePlugin",
    "ContextPlugin",
    "MathEnginePlugin",
)


@dataclass(frozen=True, slots=True)
class PluginRegistryConflictRuleSet:
    rule_set_ref: str
    live_action_patterns: tuple[str, ...] = INERT_FORBIDDEN_TOKEN_CATALOG
    legacy_runtime_patterns: tuple[str, ...] = LEGACY_RUNTIME_PATTERNS
    l6_implementation_patterns: tuple[str, ...] = L6_IMPLEMENTATION_PATTERNS
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.rule_set_ref, "PluginRegistryConflictRuleSet.rule_set_ref")
        ensure_ref_items(self.evidence_refs, "PluginRegistryConflictRuleSet.evidence_refs")
        ensure_schema_version(self.schema_version, "PluginRegistryConflictRuleSet.schema_version")


def declaration_text(value: Any) -> str:
    primitive = to_phase2_primitive(value)
    return repr(primitive)


def find_inert_pattern_hits(value: Any, patterns: tuple[str, ...]) -> tuple[str, ...]:
    text = declaration_text(value)
    return tuple(pattern for pattern in patterns if pattern in text)


def find_plain_credential_hits(value: Any) -> tuple[str, ...]:
    hits = list(suspicious_credential_value_paths(value, "registry"))
    text = declaration_text(value)
    lowered = text.lower()
    for marker in ("mockkey_", "bearer ", "akia", "password=", "api_key=", "token=", "secret="):
        if marker in lowered:
            hits.append(f"registry.value:{marker.rstrip()}")
    return tuple(hits)
