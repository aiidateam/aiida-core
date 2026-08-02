###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Interface for navigating immutable versions of a node."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiida.common import exceptions
from aiida.common.links import LinkType

from ..querybuilder import QueryBuilder

if TYPE_CHECKING:
    from .node import Node

__all__ = ('NodeVersions',)


class NodeVersions:
    """Interface to navigate the immutable versions in a node lineage."""

    def __init__(self, node: Node) -> None:
        """Initialize the versions interface.

        :param node: the node for which to navigate versions
        """
        self._node = node

    @property
    def number(self) -> int:
        """Return the version number of this node in its lineage."""
        return self._node.backend_entity.version or 1

    @property
    def lineage_uuid(self) -> str:
        """Return the stable UUID identifying this node's version lineage."""
        return self._node.backend_entity.lineage_uuid or self._node.uuid

    @property
    def is_head(self) -> bool:
        """Return whether this node is the latest version of its lineage."""
        return self.next is None

    @property
    def head(self) -> Node:
        """Return the latest version of this node's lineage."""
        versions = self.all()
        return versions[-1]

    @property
    def first(self) -> Node:
        """Return the first version of this node's lineage."""
        versions = self.all()
        return versions[0]

    @property
    def previous(self) -> Node | None:
        """Return the previous version in the lineage, if it exists."""
        if not self._node.is_stored:
            return None

        link = self._node.base.links.get_incoming(link_type=LinkType.NEXT_VERSION).first()
        return None if link is None else link.node

    @property
    def next(self) -> Node | None:
        """Return the next version in the lineage, if it exists."""
        if not self._node.is_stored:
            return None

        link = self._node.base.links.get_outgoing(link_type=LinkType.NEXT_VERSION).first()
        return None if link is None else link.node

    def get(self, version: Any) -> Node:
        """Return a specific version in the lineage.

        :param version: the version number to load
        :raises TypeError: if the version number is not an integer
        :raises ValueError: if the version number is smaller than one
        :raises aiida.common.exceptions.NotExistent: if the version does not exist
        """
        if not isinstance(version, int):
            msg = f'version should be an integer, got {type(version)}'
            raise TypeError(msg)
        if version < 1:
            msg = 'version should be larger than zero'
            raise ValueError(msg)

        for node in self.all():
            if node.base.versions.number == version:
                return node

        msg = f'lineage<{self.lineage_uuid}> does not contain version {version}'
        raise exceptions.NotExistent(msg)

    def all(self) -> list[Node]:
        """Return all versions in the lineage, ordered from first to head."""
        if not self._node.is_stored:
            return [self._node]

        filters = {'or': [{'uuid': self.lineage_uuid}, {'lineage_uuid': self.lineage_uuid}]}
        builder = QueryBuilder(backend=self._node.backend)
        builder.append(type(self._node), tag='node', filters=filters, project='*')
        builder.order_by({'node': [{'version': 'asc'}]})
        return builder.all(flat=True)

    def history(self) -> list[dict[str, Any]]:
        """Return a compact description of all versions in the lineage."""
        return [
            {
                'version': node.base.versions.number,
                'uuid': node.uuid,
                'pk': node.pk,
                'ctime': node.ctime,
                'mtime': node.mtime,
            }
            for node in self.all()
        ]

    def diff(self, other: Any) -> dict[str, dict[str, Any]]:
        """Return the attribute differences between this node and another version.

        :param other: the node to compare against
        :raises TypeError: if ``other`` is not a node
        :return: added, removed, and changed attributes when going from this node to ``other``
        """
        from .node import Node

        if not isinstance(other, Node):
            msg = f'other should be a `Node` instance, got {type(other)}'
            raise TypeError(msg)

        current = self._node.base.attributes.all
        revised = other.base.attributes.all
        current_keys = set(current)
        revised_keys = set(revised)

        return {
            'added': {key: revised[key] for key in revised_keys - current_keys},
            'removed': {key: current[key] for key in current_keys - revised_keys},
            'changed': {
                key: {'old': current[key], 'new': revised[key]}
                for key in current_keys & revised_keys
                if current[key] != revised[key]
            },
        }
