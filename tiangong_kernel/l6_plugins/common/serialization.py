"""Deterministic L6 common serialization helpers."""

from __future__ import annotations

from typing import Any

from ._common import stable_digest, stable_json, stable_primitive


def to_l6_primitive(value: Any) -> Any:
    return stable_primitive(value)


def to_l6_json(value: Any) -> str:
    return stable_json(value)


def to_l6_digest(value: Any) -> str:
    return stable_digest(value)
