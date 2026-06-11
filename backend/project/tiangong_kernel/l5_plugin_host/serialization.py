"""Deterministic L5 serialization helpers.

The helpers convert in-memory data shells to stable primitives only. They do
not read directories, scan plugin packages, or persist registry state. Phase 2
also supports manifest-like namespace payloads created in memory.
"""

from __future__ import annotations

from typing import Any

from ._common import stable_digest, stable_json
from .phase2_common import to_phase2_primitive


def to_l5_primitive(value: Any) -> Any:
    return to_phase2_primitive(value)


def to_l5_json(value: Any) -> str:
    import json

    return json.dumps(to_l5_primitive(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def to_l5_digest(value: Any) -> str:
    return stable_digest(to_l5_primitive(value))
