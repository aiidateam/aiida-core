from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict
import importlib

from pydantic import BaseModel


def is_structured_instance(value: Any) -> bool:
    """Return True for dataclass or Pydantic model instances."""
    return (is_dataclass(value) and not isinstance(value, type)) or isinstance(
        value, BaseModel
    )


def structured_to_dict(value: Any) -> Any:
    """Convert structured instances to plain dicts for namespace wiring."""
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, BaseModel):
        if contains_tagged_value(value):
            return {
                name: structured_to_dict(getattr(value, name))
                for name in value.model_fields
            }
        return value.model_dump(exclude_none=False)
    return value


def structured_type_info(tp: Any) -> Dict[str, str] | None:
    """Return a serializable descriptor for structured types."""
    if is_dataclass(tp):
        return {"kind": "dataclass", "path": structured_type_path(tp)}
    if isinstance(tp, type) and issubclass(tp, BaseModel):
        return {"kind": "pydantic", "path": structured_type_path(tp)}
    return None


def structured_type_path(tp: Any) -> str:
    return f"{tp.__module__}.{tp.__qualname__}"


def import_structured_type(path: str) -> Any:
    module_path, _, attr_path = path.rpartition(".")
    module = importlib.import_module(module_path)
    current = module
    for part in attr_path.split("."):
        current = getattr(current, part)
    return current


def coerce_structured_value(value: Any, info: Dict[str, str] | None) -> Any:
    """Rebuild a structured instance from a dict when spec says so."""
    if info is None:
        return value
    if is_structured_instance(value):
        return value
    if not isinstance(value, dict):
        return value
    cls = import_structured_type(info["path"])
    kind = info.get("kind")
    if kind == "pydantic":
        if contains_tagged_value(value):
            if hasattr(cls, "model_construct"):
                return cls.model_construct(**value)
            return cls(**value)
        if hasattr(cls, "model_validate"):
            return cls.model_validate(value)
        return cls(**value)
    if kind == "dataclass":
        return cls(**value)
    return value


def coerce_inputs_from_spec(values: Any, spec: Any) -> Any:
    """Coerce dict inputs into structured instances based on spec metadata."""
    if not isinstance(values, dict):
        return values
    try:
        from aiida.node_graph.socket_spec import SocketSpec
    except Exception:
        return values
    spec_obj = spec if isinstance(spec, SocketSpec) else SocketSpec.from_dict(spec)
    out = dict(values)
    for name, child in (spec_obj.fields or {}).items():
        if name not in out:
            continue
        info = child.meta.extras.get("structured_type")
        if info:
            out[name] = coerce_structured_value(out[name], info)
            continue
        if child.is_namespace() and isinstance(out[name], dict):
            out[name] = coerce_inputs_from_spec(out[name], child)
    return out


def contains_tagged_value(value: Any) -> bool:
    """Return True if any TaggedValue appears in the structure."""
    from aiida.node_graph.socket import TaggedValue

    if isinstance(value, TaggedValue):
        return True
    if isinstance(value, BaseModel):
        return any(
            contains_tagged_value(getattr(value, name)) for name in value.model_fields
        )
    if is_dataclass(value) and not isinstance(value, type):
        for field in value.__dataclass_fields__.values():
            if contains_tagged_value(getattr(value, field.name)):
                return True
        return False
    if isinstance(value, dict):
        return any(contains_tagged_value(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(contains_tagged_value(v) for v in value)
    return False
