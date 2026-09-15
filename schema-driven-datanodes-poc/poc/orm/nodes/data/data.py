###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Public data-node base class for the PoC."""

from __future__ import annotations

import typing as t

from poc.orm._core.nodes.data.node import Data as CoreData
from poc.orm.nodes.data.schema import FieldSpec, SchemaSpec, validate_values
from poc.storage import get_profile
from poc.storage.sqlite_temp.schema_store import load_node_values, load_schema, store_node, store_schema

__all__ = ('Data',)


class Data(CoreData):
    """Public data-node base class for schema-driven data nodes."""

    schema_spec: t.ClassVar[SchemaSpec] = SchemaSpec(name='Data', fields=())

    def store(self) -> int:
        """Store this node against the current schema version and return its id."""
        format_version, schema = type(self)._load_schema()
        values = {'label': self.label, **self.values}
        return store_node(
            get_profile(), schema, validate_values(schema, values), format_version=format_version
        )

    @classmethod
    def install_schema(cls, *, format_version: int = 1) -> None:
        """Store this class's schema declaration in the database."""
        store_schema(get_profile(), cls.schema_spec, format_version=format_version)

    @classmethod
    def _ensure_schema_installed(cls) -> None:
        """Install the schema on first use if it is not stored yet."""
        try:
            load_schema(get_profile(), cls.schema_name)
        except KeyError:
            cls.install_schema()

    @classmethod
    def _load_schema(cls) -> tuple[int, SchemaSpec]:
        """Load this class's schema declaration from the database."""
        cls._ensure_schema_installed()
        return load_schema(get_profile(), cls.schema_name)

    @classmethod
    def _from_payload(cls, payload: dict[str, t.Any]) -> t.Self:
        """Validate a payload against the stored schema and construct the node."""
        _, schema = cls._load_schema()
        values = validate_values(schema, payload)
        return cls.from_values(values)

    @classmethod
    def fields(cls) -> tuple[FieldSpec, ...]:
        """Return the fields of the stored schema for display or inspection."""
        _, schema = cls._load_schema()
        return schema.fields


def load_node(node_id: int, node_class: type[Data]) -> Data:
    """Load one stored node by id and reconstruct it as the requested class."""
    schema_name, values = load_node_values(get_profile(), node_id)
    if schema_name != node_class.schema_name:
        msg = f'node {node_id} has schema {schema_name!r}, not {node_class.schema_name!r}'
        raise ValueError(msg)
    return node_class.from_values(values)
