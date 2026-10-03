"""The core entity. Mirrors ``aiida.orm.nodes.node``.

Everything here is a :class:`ColumnField`, because these are the columns the storage schema
actually has. Their Python accessors are hand-written properties, so the declarations live in
``_column_fields`` and exist to describe and to query, not to read.

The two ways into the backend are the two a declaration uses: ``backend_entity`` for the columns,
``base.attributes`` for the open namespace one of those columns holds.
"""

from __future__ import annotations

import datetime
import typing as t
from collections.abc import Mapping, Sequence
from functools import cached_property

from poc.orm._core.entities import Entity
from poc.orm._core.fields import BaseField, ColumnField
from poc.orm._core.implementation import BackendNode
from poc.orm._core.nodes.attributes import NodeAttributes
from poc.orm._core.nodes.columns import EntityColumns
from poc.orm._core.qb_fields import QbAttributesField, QbField

__all__ = ('Node', 'NodeBase')


def _no_newlines(value: str) -> str:
    """Reject a label that would break every listing that prints one per line."""
    if '\n' in value:
        msg = f'a label may not contain a newline, got {value!r}'
        raise ValueError(msg)
    return value


class NodeBase:
    """The namespace of a node's sub-managers, reached as ``node.base``."""

    def __init__(self, node: Node) -> None:
        self._node = node

    @cached_property
    def attributes(self) -> NodeAttributes:
        """Return an interface to interact with the attributes of this node."""
        return NodeAttributes(self._node)

    @cached_property
    def columns(self) -> EntityColumns:
        """Return an interface to interact with the columns of this node."""
        return EntityColumns(self._node)


class Node(Entity):
    """An entity backed by a row: fixed columns plus an open attributes blob."""

    _column_fields: t.ClassVar[Sequence[BaseField]] = (
        ColumnField('uuid', str, 'The UUID of the node', rest_api_read_only=True),
        ColumnField('label', str, 'The node label', default='', validator=_no_newlines),
        ColumnField('ctime', datetime.datetime, 'The creation time of the node', rest_api_read_only=True),
        ColumnField('attributes', dict[str, t.Any], 'The node attributes', default_factory=dict),
    )

    def __init__(self, **columns: t.Any) -> None:
        self.backend_entity = BackendNode(**columns)

    @cached_property
    def base(self) -> NodeBase:
        """Return the namespace of this node's sub-managers."""
        return NodeBase(self)

    @property
    def uuid(self) -> str:
        return self.base.columns.get('uuid')

    @property
    def label(self) -> str:
        return self.base.columns.get('label')

    @label.setter
    def label(self, value: str) -> None:
        self.base.columns.set('label', value)

    @classmethod
    def _build_query_fields(cls, declarations: Mapping[str, BaseField]) -> dict[str, QbField]:
        """Expose the attribute-backed fields as children of the ``attributes`` field."""
        fields = super()._build_query_fields(declarations)
        children = {name: field for name, field in fields.items() if declarations[name].is_attribute}
        fields['attributes'] = QbAttributesField(declarations['attributes'], children)
        return fields
