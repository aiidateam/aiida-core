from __future__ import annotations
from typing import Optional, Dict, Any, Literal
from copy import deepcopy
from aiida.node_graph.socket_spec import SocketSpec
from aiida.node_graph.orm.mapping import type_mapping as default_type_mapping
from aiida.node_graph.socket_meta import SocketMeta
from dataclasses import MISSING


def _spec_shape_snapshot(
    spec: SocketSpec, type_mapping: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Build a minimal, UI-friendly snapshot of a SocketSpec so runtime sockets
    expose their structure via `socket._metadata.extras`.

    Shape:
      Leaf:
        { "identifier": "...", "default": <value?> }
      Namespace:
        {
          "identifier": "...",
          "dynamic": true,                           # if dynamic
          "item": <snapshot>,                        # if dynamic (item present)
        }
    """
    type_mapping = type_mapping or default_type_mapping
    d: Dict[str, Any] = {"identifier": spec.identifier}

    if spec.identifier == type_mapping["namespace"]:
        # dynamic behavior
        if spec.dynamic:
            d["dynamic"] = True
            if spec.item is not None:
                d["item"] = spec.item.to_dict()
            else:
                d["item"] = None
    else:
        # leaf: include default if present
        if not isinstance(getattr(spec, "default", MISSING), type(MISSING)):
            d["default"] = deepcopy(spec.default)

    return d


def runtime_meta_from_spec(
    spec: SocketSpec,
    *,
    role: Literal["input", "output"],
    arg_role: Optional[str] = None,
    is_builtin: bool = False,
    function_generated: bool = False,
    link_limit_for_dynamic: int = 1_000_000,
    extra_overrides: Optional[Dict[str, Any]] = None,
    type_mapping: Dict[str, Any] = None,
) -> SocketMeta:
    """
    Convert an author-time SocketSpec to runtime SocketMeta (engine-facing).
    Also emits a shape snapshot into `extras` so tests and UIs can introspect:
      - extras["identifier"]
      - extras["sockets"] for fixed namespace fields
      - extras["dynamic"] + extras["item"] for dynamic namespaces
      - extras["default"] on leaves (optional)
      - extras["widget"] when present on the spec
    """
    type_mapping = type_mapping or default_type_mapping
    is_namespace = spec.identifier == type_mapping["namespace"]
    child_link_limit = spec.meta.child_default_link_limit
    if child_link_limit is None:
        child_link_limit = link_limit_for_dynamic if spec.dynamic else 1

    chosen_role = (
        arg_role or spec.meta.call_role or ("kwargs" if role == "input" else "return")
    )

    extras: Dict[str, Any] = _spec_shape_snapshot(spec, type_mapping=type_mapping)
    extras.update({k: v for k, v in spec.meta.extras.items() if k not in extras})

    if extra_overrides:
        extras.update(extra_overrides)

    extras.setdefault("builtin_socket", bool(is_builtin))
    extras.setdefault("function_socket", bool(function_generated))

    return SocketMeta(
        help=spec.meta.help,
        required=spec.meta.required,
        call_role=spec.meta.call_role,
        is_metadata=spec.meta.is_metadata,
        dynamic=bool(spec.dynamic) if is_namespace else False,
        child_default_link_limit=child_link_limit,
        socket_type="INPUT" if role == "input" else "OUTPUT",
        arg_type=chosen_role,
        extras=extras,
    )
