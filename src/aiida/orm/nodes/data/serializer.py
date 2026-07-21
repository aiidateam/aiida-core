###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Serialize arbitrary Python values into AiiDA data nodes.

This is the generic value-to-node serialization service shared by function-based calculations and the WorkGraph
engine. It layers three strategies:

1. :func:`~aiida.orm.nodes.data.base.to_aiida_type` for the value types core owns (the ``BaseType`` scalars, lists,
   dicts, numpy scalars and arrays, enums and ``None``), dispatched by type.
2. an entry-point-driven registry for types core does not own, so a plugin can serialize a type it does not import.
3. :class:`~aiida.orm.nodes.data.jsonable.JsonableData` as a JSON-able last resort.
"""

from __future__ import annotations

import functools
import typing as t
from importlib import import_module

from .base import to_aiida_type
from .jsonable import JsonableData

if t.TYPE_CHECKING:
    from aiida.orm import User

__all__ = ('general_serializer', 'serialize_to_aiida_nodes')


def import_from_path(path: str) -> t.Any:
    """Import and return the object referenced by a ``module.qualname`` path.

    :param path: dotted path whose last segment is the attribute name, e.g. ``aiida.orm.nodes.data.list.List``.
    :raises AttributeError: if the attribute does not exist in the resolved module.
    """
    module_name, object_name = path.rsplit('.', 1)
    module = import_module(module_name)
    try:
        return getattr(module, object_name)
    except AttributeError as exc:
        msg = f'`{object_name}` not found in module `{module_name}`.'
        raise AttributeError(msg) from exc


@functools.cache
def get_serializers() -> dict[str, str]:
    """Return the ``{type_key: import_path}`` serializer registry built from the ``aiida.data`` entry points.

    The entry-point *name* encodes the value type it serializes: the first dotted segment is a namespace and the rest
    is the value's ``f'{type.__module__}.{type.__name__}'`` key. For example ``core.none`` registered as
    ``pythonjob.builtins.NoneType`` yields the key ``builtins.NoneType``. Names without a dot after the namespace are
    plain class registrations (``core.dict``, ``core.array``), not type serializers, and are skipped; hierarchical
    core names (``core.array.bands``) yield keys that match no real value type and are harmless.

    Built-in and numpy value types are intentionally absent here: they are served by :func:`to_aiida_type`. The result
    is cached; on the rare competing registration for one key the lexicographically first import path wins so the
    choice is deterministic. Pass an explicit ``serializers`` mapping to :func:`general_serializer` to override.
    """
    from aiida.plugins.entry_point import get_entry_points

    grouped: dict[str, list[str]] = {}
    for entry_point in get_entry_points('aiida.data'):
        key = entry_point.name.split('.', 1)[-1]
        if '.' not in key:
            continue
        grouped.setdefault(key, []).append(entry_point.value.replace(':', '.'))

    return {key: sorted(paths)[0] for key, paths in grouped.items()}


def general_serializer(
    data: t.Any,
    serializers: dict[str, str] | None = None,
    store: bool = True,
    user: User | None = None,
) -> t.Any:
    """Serialize a single Python value to an AiiDA data node.

    Existing nodes and :class:`~aiida.common.extendeddicts.AttributeDict` namespaces are returned unchanged. Otherwise
    the value is converted through :func:`to_aiida_type` (core-owned types), then the entry-point registry (foreign
    types), then :class:`JsonableData` (JSON-able objects), raising :class:`ValueError` with guidance if none applies.

    :param data: the value to serialize.
    :param serializers: optional ``{type_key: import_path}`` override; defaults to :func:`get_serializers`.
    :param store: whether to store the created node (an already-existing node is never re-stored).
    :param user: the user to assign to a newly created node.
    :raises ValueError: if the value cannot be serialized by any strategy.
    """
    from aiida.common.extendeddicts import AttributeDict
    from aiida.orm import Node

    if serializers is None:
        serializers = get_serializers()

    if isinstance(data, Node):
        return data
    if isinstance(data, AttributeDict):
        return data

    # Core-owned value types (scalars, list, dict, numpy, enum, None) dispatch by type through ``to_aiida_type``.
    try:
        node = to_aiida_type(data)
    except TypeError:
        node = None
    if node is not None:
        if store:
            node.store()
        return node

    # Foreign / plugin-owned types resolved by their ``aiida.data`` entry-point registration.
    type_key = f'{type(data).__module__}.{type(data).__name__}'
    if type_key in serializers:
        try:
            serializer = import_from_path(serializers[type_key])
            new_node = serializer(data, user=user)
        except Exception as exc:
            # A plugin-provided serializer may raise anything; wrap it with context about which registration failed.
            msg = f'error serializing `{type_key}` with `{serializers[type_key]}`: {exc}'
            raise ValueError(msg) from exc
        if store:
            new_node.store()
        return new_node

    # Last resort: wrap any JSON-representable object.
    try:
        node = JsonableData(data, user=user)
    except (TypeError, ValueError) as exc:
        msg = (
            f'cannot serialize the object of type `{type_key}`.\n'
            'To fix this, either:\n'
            '  1. register a type-specific `aiida.orm.Data` subclass as an `aiida.data` entry point, or\n'
            '  2. make the class JSON-able for `JsonableData` (an `as_dict`/`to_dict` method plus a `from_dict`\n'
            '     class method, or make it a dataclass or pydantic model), or\n'
            "  3. pass an ad-hoc serializer through `serializers`, e.g. {'my_pkg.MyType': 'my_pkg:to_aiida_node'}."
        )
        raise ValueError(msg) from exc
    if store:
        node.store()
    return node


def serialize_to_aiida_nodes(inputs: dict[str, t.Any], serializers: dict[str, str] | None = None) -> dict[str, t.Any]:
    """Serialize each value of a mapping to an AiiDA data node with :func:`general_serializer`."""
    return {key: general_serializer(value, serializers=serializers) for key, value in inputs.items()}
