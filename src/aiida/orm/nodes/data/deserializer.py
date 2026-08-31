###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Deserialize AiiDA data nodes back into raw Python values.

This is the inverse of :func:`~aiida.orm.nodes.data.serializer.general_serializer`. A node that exposes a ``value``
is returned directly; otherwise a registry keyed by the node's ``module.ClassName`` maps it to a deserializer. Nested
mappings are walked recursively.
"""

from __future__ import annotations

import functools
import typing as t

#: Deserializers for node types that do not expose a ``value`` attribute, keyed by the node class import path and
#: mapping to the import path of a ``(node) -> value`` callable.
BUILTIN_DESERIALIZERS: dict[str, str] = {
    'aiida.orm.nodes.data.list.List': 'aiida.orm.nodes.data.deserializer.list_data_to_list',
    'aiida.orm.nodes.data.dict.Dict': 'aiida.orm.nodes.data.deserializer.dict_data_to_dict',
    'aiida.orm.nodes.data.array.array.ArrayData': 'aiida.orm.nodes.data.deserializer.array_data_to_array',
    'aiida.orm.nodes.data.structure.StructureData': 'aiida.orm.nodes.data.deserializer.structure_data_to_atoms',
}

__all__ = ('deserialize_to_raw_python_data',)


def list_data_to_list(data):
    return data.get_list()


def dict_data_to_dict(data):
    return data.get_dict()


def array_data_to_array(data):
    return data.get_array()


def structure_data_to_atoms(structure):
    """Return the ASE ``Atoms`` of a ``StructureData`` (requires ``ase`` at call time)."""
    return structure.get_ase()


def structure_data_to_pymatgen(structure):
    """Return the pymatgen structure of a ``StructureData`` (requires ``pymatgen`` at call time)."""
    return structure.get_pymatgen()


@functools.cache
def get_deserializers() -> dict[str, str]:
    """Return the ``{node_type_path: deserializer_path}`` registry (cached)."""
    return dict(BUILTIN_DESERIALIZERS)


def deserialize_to_raw_python_data(
    data: t.Any,
    deserializers: dict[str, str] | None = None,
    dry_run: bool = False,
) -> t.Any:
    """Deserialize an AiiDA data node (or nested mapping of nodes) back into raw Python values.

    A node exposing a ``value`` attribute is returned through it; otherwise the ``deserializers`` registry maps the
    node type to a deserializer. Mappings are walked recursively.

    :param data: the node or nested mapping to deserialize.
    :param deserializers: optional ``{node_type_path: deserializer_path}`` override; defaults to
        :func:`get_deserializers`.
    :param dry_run: if true, return ``None`` for ``value``-exposing leaves instead of reading them (used to validate
        deserializability without materializing values).
    :raises ValueError: if a node exposes no ``value`` and no matching deserializer is registered.
    """
    from plumpy.utils import AttributesFrozendict

    from aiida import common, orm

    from .serializer import import_from_path

    if deserializers is None:
        deserializers = get_deserializers()

    if isinstance(data, orm.Data):
        if hasattr(data, 'value'):
            return None if dry_run else data.value
        type_key = f'{type(data).__module__}.{type(data).__name__}'
        if type_key in deserializers:
            deserializer = import_from_path(deserializers[type_key])
            return deserializer(data)
        msg = (
            f'cannot deserialize an AiiDA data node of type `{type_key}`: it exposes no `value` attribute and no '
            f'matching deserializer is registered. Use a data type with a `value`, or provide one through '
            f"`deserializers`, e.g. {{'{type_key}': 'my_pkg:my_deserializer'}}."
        )
        raise ValueError(msg)

    if isinstance(data, (common.extendeddicts.AttributeDict, AttributesFrozendict, dict)):
        return {key: deserialize_to_raw_python_data(value, deserializers=deserializers) for key, value in data.items()}

    return None
