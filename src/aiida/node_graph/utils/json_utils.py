from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel


def json_ready(value: Any) -> Any:
    """Convert a value into a JSON-serialisable structure."""

    if is_dataclass(value):
        return json_ready(asdict(value))
    if isinstance(value, BaseModel):
        return json_ready(value.model_dump(exclude_none=True))
    if isinstance(value, Enum):
        return json_ready(value.value)
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_ready(v) for v in value]
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def stable_json_dumps(value: Any) -> str:
    """Return a stable JSON string for hashing/deduplication."""

    try:
        return json.dumps(value, sort_keys=True, default=str)
    except Exception:
        return repr(value)


def hashable_signature(value: Any) -> Any:
    """Return a hashable representation of a JSON-ready object."""

    if isinstance(value, (dict, list)):
        return stable_json_dumps(value)
    return value


def triple_signature(triple: Any) -> tuple[Any, ...]:
    """Return a hashable signature for triple-like objects.

    This is used for deduplicating triples where the object might be a list/dict
    (i.e. JSON-ready but not hashable).
    """
    if isinstance(triple, (list, tuple)) and len(triple) == 3:
        subject, predicate, obj = triple
        return (subject, predicate, hashable_signature(obj))
    if isinstance(triple, (list, tuple)):
        return tuple(hashable_signature(value) for value in triple)
    return (hashable_signature(triple),)
