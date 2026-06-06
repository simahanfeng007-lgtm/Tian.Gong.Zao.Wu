"""L6 common contract validators and deterministic helpers.

This module is deliberately inert. It validates in-memory declaration values
only and never touches files, networks, model SDKs, tools, credentials, lower
layer state, registries, or plugin code.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any

L6_COMMON_SCHEMA_VERSION = "0.1"
L6_SOURCE_LAYER = "L6"
MAX_REF_LENGTH = 256
MAX_SUMMARY_LENGTH = 768
MAX_DIGEST_LENGTH = 128

REF_PREFIXES = (
    "ref:",
    "decl:",
    "summary:",
    "digest:",
    "policy:",
    "budget:",
    "audit:",
    "credential-policy:",
    "context:",
    "projection:",
    "event:",
    "handoff:",
    "l3:",
    "l4:",
    "l5:",
    "l6:",
    "l6_phase1:",
    "l6_phase2:",
    "l6_phase3:",
    "l6_phase4:",
    "l6_phase5:",
    "l6_common:",
    "test:",
    "evidence:",
    "invariant:",
    "forbid:",
    "migration:",
    "rollback:",
    "hotswitch:",
    "quality:",
    "responsibility:",
    "public:",
    "state:",
    "model-cap:",
    "tool-cap:",
    "permission:",
    "lifecycle:",
    "score:",
    "suggestion:",
    "hint:",
    "report:",
    "request:",
    "requirement:",
    "review:",
    "mind:",
    "affective:",
    "emotion:",
    "desire:",
    "attention:",
    "preference:",
    "memory:",
    "fact:",
    "world:",
    "belief:",
    "goal:",
    "actor:",
    "run:",
    "checkpoint:",
    "validation:",
    "regression:",
    "formula:",
    "weight:",
    "redaction:",
    "redact:",
    "product:",
    "learning:",
    "healing:",
    "resource:",
    "quota:",
    "limiter:",
)

LIVE_ADDRESS_MARKERS = (
    "://",
    "http:",
    "https:",
    "file:",
    "ws:",
    "wss:",
    "postgres:",
    "mysql:",
    "mongodb:",
    "redis:",
)

LIVE_EXECUTION_MARKERS = (
    "module:function",
    "importlib.",
    "subprocess",
    "os.system",
    "popen",
    "shell=True",
    "powershell",
    "cmd.exe",
    "bash ",
    "sh ",
    "Path.write_text",
    "Path.unlink",
    "shutil.rmtree",
    "socket.",
    "requests.",
    "httpx.",
    "urllib.request",
    "sqlite3.connect",
)

SENSITIVE_VALUE_MARKERS = (
    "api_key=",
    "apikey=",
    "access_token=",
    "refresh_token=",
    "secret=",
    "password=",
    "private_key=",
    "bearer ",
    "sk-",
    "x-api-key",
    "database_uri=",
)

FORBIDDEN_FIELD_NAMES = frozenset(
    (
        "entrypoint",
        "entry_point",
        "callable",
        "handler",
        "function",
        "module_function",
        "shell_command",
        "command",
        "provider_base_url",
        "base_url",
        "endpoint",
        "api_key",
        "token",
        "password",
        "secret",
        "secret_value",
        "credential_value",
        "file_path",
        "database_uri",
        "tool_handle",
        "model_client",
        "l4_adapter",
        "state_writer",
        "audit_writer",
    )
)

ALLOWED_PROVIDER_NEUTRAL_HINTS = (
    "deepseek_v4",
    "xiaomi_mimo",
    "glm_5_1",
    "minimax_m3",
    "gpt_5_5",
)


def ensure_bool(value: bool, field_name: str) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be boolean")


def ensure_score(value: float, field_name: str, *, minimum: float = 0.0, maximum: float = 1.0) -> None:
    """Validate an inert normalized score.

    Python treats ``bool`` as an ``int`` subclass. L6.40 makes that explicit:
    booleans are control flags, never numeric score factors. This helper is
    side-effect-free and suitable for kernel declaration objects.
    """

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric score, not bool")
    numeric = float(value)
    if numeric != numeric or numeric < minimum or numeric > maximum:
        raise ValueError(f"{field_name} must be within {minimum}..{maximum}")


def ensure_short_text(value: str, field_name: str, limit: int = MAX_SUMMARY_LENGTH) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be text")
    if "\x00" in value:
        raise ValueError(f"{field_name} cannot contain null byte")
    if len(value) > limit:
        raise ValueError(f"{field_name} exceeds L6 common text limit")


def ensure_non_empty_text(value: str, field_name: str, limit: int = MAX_REF_LENGTH) -> None:
    ensure_short_text(value, field_name, limit)
    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty")


def ensure_schema_version(value: str, field_name: str = "schema_version") -> None:
    ensure_non_empty_text(value, field_name, 32)


def ensure_ref_text(value: str, field_name: str, *, required: bool = True) -> None:
    if value == "" and not required:
        return
    ensure_non_empty_text(value, field_name, MAX_REF_LENGTH)
    if any(marker in value for marker in ("\n", "\r", "\x00")):
        raise ValueError(f"{field_name} must be compact ref text")
    lowered = value.lower()
    if any(marker in lowered for marker in LIVE_ADDRESS_MARKERS):
        raise ValueError(f"{field_name} cannot contain live address marker")
    if "/" in value or "\\" in value:
        raise ValueError(f"{field_name} cannot contain filesystem path separators")
    # Namespaced references should use one of the public inert prefixes.
    # Legacy compact literals such as enum values remain valid when they do
    # not use a colon namespace. This keeps historical contracts compatible
    # while making REF_PREFIXES an active guard for ref-like values.
    if ":" in value and not value.startswith(REF_PREFIXES):
        raise ValueError(f"{field_name} must use an allowed inert ref prefix")


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


def ensure_ref_or_summary_items(items: tuple[str, ...], field_name: str, *, required: bool = False) -> None:
    if not isinstance(items, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if required and not items:
        raise ValueError(f"{field_name} cannot be empty")
    for item in items:
        ensure_short_text(item, field_name, MAX_SUMMARY_LENGTH)
        ensure_no_live_or_sensitive_text(item, field_name)


def ensure_digest(value: str, field_name: str, *, required: bool = False) -> None:
    if value == "" and not required:
        return
    ensure_non_empty_text(value, field_name, MAX_DIGEST_LENGTH)
    if len(value) not in (32, 40, 64, 128):
        raise ValueError(f"{field_name} must look like compact digest")
    if not all(char in "0123456789abcdefABCDEF" for char in value):
        raise ValueError(f"{field_name} must be hex-like")


def ensure_no_live_or_sensitive_text(value: str, field_name: str) -> None:
    ensure_short_text(value, field_name, MAX_SUMMARY_LENGTH)
    lowered = value.lower()
    if any(marker in lowered for marker in LIVE_ADDRESS_MARKERS):
        raise ValueError(f"{field_name} cannot contain live address")
    if any(marker.lower() in lowered for marker in LIVE_EXECUTION_MARKERS):
        raise ValueError(f"{field_name} cannot contain live execution marker")
    if any(marker in lowered for marker in SENSITIVE_VALUE_MARKERS):
        raise ValueError(f"{field_name} cannot contain sensitive value marker")
    if "=" in value and any(word in lowered for word in ("token", "secret", "password", "api_key", "apikey")):
        raise ValueError(f"{field_name} cannot contain inline credential assignment")


def ensure_safe_free_text_items(items: tuple[str, ...], field_name: str, *, required: bool = False) -> None:
    if not isinstance(items, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if required and not items:
        raise ValueError(f"{field_name} cannot be empty")
    for item in items:
        ensure_no_live_or_sensitive_text(item, field_name)


def ensure_field_names_are_safe(value: Any, field_path: str = "value") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name in FORBIDDEN_FIELD_NAMES:
                raise ValueError(f"{field_path}.{field.name} is forbidden in L6 common contracts")
            ensure_field_names_are_safe(getattr(value, field.name), f"{field_path}.{field.name}")
    elif isinstance(value, tuple):
        for index, item in enumerate(value):
            ensure_field_names_are_safe(item, f"{field_path}[{index}]")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            ensure_field_names_are_safe(item, f"{field_path}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            if str(key) in FORBIDDEN_FIELD_NAMES:
                raise ValueError(f"{field_path}.{key} is forbidden in L6 common contracts")
            ensure_field_names_are_safe(item, f"{field_path}.{key}")


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
    raise TypeError(f"unsupported L6 common value: {type(value).__name__}")


def stable_json(value: Any) -> str:
    return json.dumps(stable_primitive(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def stable_digest(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def validate_provider_neutral_hints(hints: tuple[str, ...], field_name: str = "provider_neutral_hints") -> None:
    ensure_text_items(hints, field_name, limit=64)
    for hint in hints:
        if hint != hint.lower():
            raise ValueError(f"{field_name} must be lowercase provider-neutral hints")
        if hint not in ALLOWED_PROVIDER_NEUTRAL_HINTS:
            raise ValueError(f"{field_name} contains unsupported provider-neutral hint: {hint!r}")


def dataclass_digest(value: Any, excluded: tuple[str, ...] = ()) -> str:
    if not is_dataclass(value) or isinstance(value, type):
        raise TypeError("dataclass_digest requires a dataclass instance")
    payload = {field.name: getattr(value, field.name) for field in fields(value) if field.name not in excluded}
    return stable_digest(payload)
