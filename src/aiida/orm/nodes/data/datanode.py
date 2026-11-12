###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Shared base class for data-like nodes: :class:`~aiida.orm.Data` and owned containers."""

from __future__ import annotations

import typing as t

from aiida.orm.nodes.node import Node

if t.TYPE_CHECKING:
    from typing_extensions import Self

__all__ = ('DataNode',)


class DataNode(Node):
    """Abstract common base class for all data-like nodes.

    Both :class:`~aiida.orm.Data` nodes and owned containers
    (:class:`~aiida.orm.Container`, i.e. ``DataList``/``DataDict``) are data nodes: they share node identity (a
    ``DbNode`` row, a ``data.``-prefixed ``node_type`` string, provenance links) and are accepted anywhere
    provenance carries data — process inputs and outputs, ``CREATE``/``INPUT_*``/``RETURN`` links, and
    :class:`~aiida.orm.QueryBuilder` data queries.

    The two branches keep separate storage implementations: ``Data`` persists through ``BackendNode.store`` while
    containers persist through the dedicated ``BackendContainer`` storage entity (``store_container``). This class
    itself is abstract: it has no entry point and cannot be stored. Querying it matches both branches; querying
    ``Data`` excludes containers and querying ``Container`` matches ``DataList`` and ``DataDict``.
    """

    # Abstract base: no entry point, never stored directly. Concrete branches opt back in.
    _storable = False
    _unstorable_message = 'DataNode is an abstract base class and cannot be stored'

    def clone(self) -> Self:
        """Create an independent, unstored copy of this data node.

        The copy has a new identity and carries no provenance links of the source. For containers the copy is
        recursive over the owned subtree. Mutable metadata is independent between the copies.

        :returns: an unstored copy of this data node.
        """
        raise NotImplementedError
