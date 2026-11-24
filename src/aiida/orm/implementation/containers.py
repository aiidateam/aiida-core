###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Abstract ``BackendContainer`` storage entity for owned data containers.

Containers share the common node identity (``DbNode`` row, ``node_type``
string, provenance links) but are decoupled from ``Data`` semantics:
they are never persisted through :meth:`BackendNode.store
<aiida.orm.implementation.nodes.BackendNode.store>`. Leaf data goes
through ``BackendNode.store``; containers go through
:meth:`BackendContainer.store_container`, which writes the same
``DbNode`` row through a dedicated code path so container persistence
can evolve independently of data persistence.
"""

from __future__ import annotations

import abc
import typing as t
from collections.abc import Sequence

from aiida.orm.implementation.nodes import BackendNode

if t.TYPE_CHECKING:
    from typing_extensions import Self

    from aiida.orm.utils import LinkTriple

__all__ = ('BackendContainer',)


class BackendContainer(BackendNode, metaclass=abc.ABCMeta):
    """Backend entity for an owned data container (``DataList``/``DataDict``).

    Shares the ``BackendNode`` interface (common node identity) but
    replaces the persistence contract: use :meth:`store_container` for
    containers, never :meth:`store`. The generic ``store`` is overridden
    to raise so accidental reuse of the data path fails loudly instead
    of silently persisting a container as plain data.
    """

    @abc.abstractmethod
    def store_container(self, links: Sequence[LinkTriple] | None = None, clean: bool = True) -> Self:
        """Store this container node row in the database.

        Dedicated container persistence: writes the ``DbNode`` row (plus
        optional incoming provenance ``links`` for the ownership root)
        without creating any membership edges. The edges and child owner
        references are persisted atomically via
        ``backend.create_container_membership``. Must not delegate to
        :meth:`BackendNode.store`.

        :param links: optional incoming provenance links (ownership root only).
        :param clean: whether to clean attributes/extras before storing.
        """
