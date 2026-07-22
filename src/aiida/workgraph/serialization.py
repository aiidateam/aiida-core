###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Schema-driven serialization of raw Python data into AiiDA data nodes.

This is the node-graph-coupled layer of the serialization stack: it walks a :class:`node_graph.socket_spec.SocketSpec`
schema and serializes each leaf with :func:`~aiida.orm.general_serializer`, which is why it lives in the WorkGraph
subsystem (which may depend on node-graph) rather than in ``aiida.orm`` (which may not).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from node_graph.socket_meta import SocketMeta
from node_graph.socket_spec import SocketSpec
from node_graph.utils.struct_utils import is_structured_instance, structured_to_dict

from aiida.orm import general_serializer

if TYPE_CHECKING:
    from aiida.orm import User

__all__ = ('serialize_ports',)


def _ensure_spec(schema: SocketSpec | dict[str, Any]) -> SocketSpec:
    """Return ``schema`` as a :class:`SocketSpec`, building one from a dict if needed."""
    if isinstance(schema, SocketSpec):
        return schema
    if isinstance(schema, dict):
        return SocketSpec.from_dict(schema)
    msg = f'unsupported schema type: {type(schema)}'
    raise TypeError(msg)


def serialize_ports(
    python_data: Any,
    port_schema: SocketSpec | dict[str, Any],
    serializers: dict[str, str] | None = None,
    user: User | None = None,
) -> Any:
    """Serialize raw Python data into AiiDA data nodes following a :class:`SocketSpec` schema.

    A namespace spec is walked recursively, serializing each declared field and (for a ``dynamic`` namespace) any extra
    keys; metadata fields are passed through untouched. A leaf spec serializes the value directly. The produced nodes
    are not stored (the caller stores them as part of the process inputs).

    :param python_data: the raw value or nested mapping to serialize.
    :param port_schema: the socket spec describing the expected structure, or its dict form.
    :param serializers: optional ``{type_key: import_path}`` override forwarded to :func:`general_serializer`.
    :param user: the user to assign to newly created nodes.
    :raises ValueError: if a namespace value is not a mapping, or holds a key the (non-dynamic) namespace does not
        declare.
    """
    spec = _ensure_spec(port_schema)

    # Leaf: serialize the value directly.
    if not spec.is_namespace():
        return general_serializer(python_data, serializers=serializers, store=False, user=user)

    name = getattr(spec.meta, 'help', None) or '<namespace>'
    if is_structured_instance(python_data):
        python_data = structured_to_dict(python_data)
    if not isinstance(python_data, dict):
        msg = f"expected a mapping for namespace '{name}', got {type(python_data)}"
        raise ValueError(msg)

    out: dict[str, Any] = {}
    fields = spec.fields or {}

    for key, value in python_data.items():
        if key in fields:
            child_spec = fields[key]
            if child_spec.meta.is_metadata:
                # Metadata is not serialized; it is carried through verbatim.
                out[key] = value
            elif child_spec.is_namespace():
                out[key] = serialize_ports(value, child_spec, serializers=serializers, user=user)
            else:
                out[key] = general_serializer(value, serializers=serializers, store=False, user=user)
        elif spec.meta.dynamic:
            # Extra keys are allowed in a dynamic namespace; ``item`` (if given) types them, else ANY.
            if spec.item is None:
                if isinstance(value, dict):
                    item = SocketSpec(identifier='node_graph.namespace', meta=SocketMeta(dynamic=True))
                    out[key] = serialize_ports(value, item, serializers=serializers, user=user)
                else:
                    out[key] = general_serializer(value, serializers=serializers, store=False, user=user)
            elif spec.item.is_namespace():
                out[key] = serialize_ports(value, spec.item, serializers=serializers, user=user)
            else:
                out[key] = general_serializer(value, serializers=serializers, store=False, user=user)
        else:
            msg = f"unexpected key '{key}' for namespace '{name}' (not dynamic)."
            raise ValueError(msg)

    return out
