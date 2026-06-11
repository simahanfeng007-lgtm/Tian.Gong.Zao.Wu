"""Shared L5 phase 2 validators for manifest declaration shells.

The helpers in this module validate in-memory declaration values only. They do
not resolve plugins, read package files, verify signatures, issue permissions,
consume budgets, or contact external trust systems.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from ._common import ensure_bool, ensure_ref_items, ensure_ref_text, ensure_short_text, stable_primitive

L5_PLUGIN_MANIFEST_SCHEMA_VERSION = "0.2"
L5_PLUGIN_MANIFEST_PHASE = "L5.phase2"

ALLOWED_PLUGIN_KINDS = (
    "declaration",
    "manifest_only",
    "skill_surface",
    "tool_group",
    "subsystem_service",
    "context_assembler",
    "recovery_surface",
    "validation_surface",
)

ALLOWED_MOUNT_SURFACE_KINDS = (
    "skill_surface",
    "tool_group_surface",
    "subsystem_service_surface",
    "context_assembler_surface",
    "recovery_surface",
    "validation_surface",
    "manifest_only_surface",
)

SEVERITY_P0 = "P0"
SEVERITY_P1 = "P1"
SEVERITY_P2 = "P2"
SEVERITY_P3 = "P3"

_BLOCKED_EXEC_REF_FRAGMENTS = (
    "://",
    "/",
    "\\",
    " ",
    "\t",
    "\n",
    "\r",
    "$(",
    "${",
    "`",
)
_ALLOWED_ENTRY_PREFIXES = ("entry:", "decl:", "ref:", "logical:", "plugin-entry:")
_UNBOUNDED_RESOURCE_WORDS = ("unbounded", "infinite", "unlimited", "no_limit")
_PLACEHOLDER_VALUES = ("", "ref", "redacted", "placeholder", "example", "dummy", "masked", "absent")


def ensure_ref_or_empty(value: str, field_name: str) -> None:
    ensure_ref_text(value, field_name, required=False)


def ensure_required_text_tuple(items: tuple[str, ...], field_name: str) -> None:
    ensure_ref_items(items, field_name, required=True)


def ensure_optional_text_tuple(items: tuple[str, ...], field_name: str) -> None:
    ensure_ref_items(items, field_name)


def ensure_allowed_value(value: str, allowed: tuple[str, ...], field_name: str) -> None:
    ensure_short_text(value, field_name, 128)
    if value not in allowed:
        raise ValueError(f"{field_name} has unsupported value")


def ensure_semver_text(value: str, field_name: str) -> None:
    ensure_short_text(value, field_name, 64)
    parts = value.split(".")
    if len(parts) < 2 or not all(part.isdigit() for part in parts if part):
        raise ValueError(f"{field_name} must use a stable dotted numeric declaration")


def ensure_no_executable_reference(value: str, field_name: str) -> None:
    ensure_ref_text(value, field_name)
    if any(fragment in value for fragment in _BLOCKED_EXEC_REF_FRAGMENTS):
        raise ValueError(f"{field_name} must be a logical declaration ref only")
    if value.endswith((".py", ".sh", ".bat", ".exe", ".dll", ".so")):
        raise ValueError(f"{field_name} must not name executable artifacts")
    if ":" in value and not value.startswith(_ALLOWED_ENTRY_PREFIXES):
        raise ValueError(f"{field_name} must not use module:function or command-style syntax")
    if value.count(".") >= 2 and not value.startswith(("ref", "entry", "decl", "logical")):
        raise ValueError(f"{field_name} must not look like an import path")


def ensure_no_callable_object(value: Any, field_name: str) -> None:
    if callable(value):
        raise ValueError(f"{field_name} must not contain callable runtime objects")


def ensure_no_runtime_object(value: Any, field_name: str) -> None:
    ensure_no_callable_object(value, field_name)
    if hasattr(value, "fileno") or hasattr(value, "send") or hasattr(value, "recv"):
        raise ValueError(f"{field_name} must not contain runtime handles")


def ensure_no_unbounded_resource_text(value: Any, field_name: str) -> None:
    primitive = stable_primitive(value)

    def walk(node: Any) -> None:
        if isinstance(node, str):
            lowered = node.lower()
            if any(word in lowered for word in _UNBOUNDED_RESOURCE_WORDS):
                raise ValueError(f"{field_name} must not declare unlimited resources")
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for item in node.values():
                walk(item)

    walk(primitive)


def _looks_like_prefixed_secret(value: str) -> bool:
    compact = value.strip()
    lowered = compact.lower()
    model_key_prefix = "s" "k-"
    aws_prefix = "AK" "IA"
    bearer_prefix = "Bear" "er "
    private_key_marker = "BEGIN " "PRIVATE KEY"
    if compact.startswith(model_key_prefix) and len(compact) >= 12:
        return True
    if compact.startswith(aws_prefix) and len(compact) >= 16:
        return True
    if compact.startswith(bearer_prefix) and len(compact) >= 20:
        return True
    if private_key_marker in compact:
        return True
    for prefix in ("pass" "word=", "api" "_key=", "to" "ken=", "se" "cret="):
        if lowered.startswith(prefix):
            tail = compact.split("=", 1)[1].strip().lower()
            if tail not in _PLACEHOLDER_VALUES and not tail.startswith(("ref:", "handle:", "scope:")):
                return True
    return False



def to_phase2_primitive(value: Any) -> Any:
    if hasattr(value, "__dict__") and not is_dataclass(value):
        return {str(key): to_phase2_primitive(item) for key, item in sorted(vars(value).items())}
    try:
        return stable_primitive(value)
    except TypeError:
        if hasattr(value, "__dict__"):
            return {str(key): to_phase2_primitive(item) for key, item in sorted(vars(value).items())}
        raise

def suspicious_credential_value_paths(value: Any, field_path: str = "value") -> tuple[str, ...]:
    primitive = to_phase2_primitive(value)
    hits: list[str] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, str):
            if _looks_like_prefixed_secret(node):
                hits.append(path)
        elif isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{path}[{index}]")
        elif isinstance(node, dict):
            for key, item in node.items():
                # Keys are governance field names; only values are scanned here.
                walk(item, f"{path}.{key}")

    walk(primitive, field_path)
    return tuple(hits)


def ensure_no_plain_credential_values(value: Any, field_name: str) -> None:
    hits = suspicious_credential_value_paths(value, field_name)
    if hits:
        raise ValueError(f"{field_name} contains suspected plain credential values")


def ensure_dataclass_instance(value: Any, expected_type: type[Any], field_name: str, *, required: bool = True) -> None:
    if value is None and not required:
        return
    if not isinstance(value, expected_type):
        raise ValueError(f"{field_name} must be {expected_type.__name__}")


def ensure_tuple_of_dataclass(items: tuple[Any, ...], expected_type: type[Any], field_name: str, *, required: bool = False) -> None:
    if not isinstance(items, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if required and not items:
        raise ValueError(f"{field_name} cannot be empty")
    for item in items:
        ensure_dataclass_instance(item, expected_type, field_name)


def dataclass_field_names(value: Any) -> tuple[str, ...]:
    if not is_dataclass(value) or isinstance(value, type):
        return tuple()
    return tuple(field.name for field in fields(value))
