###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Node representing provenance that was intentionally removed."""

from __future__ import annotations

from aiida.common import exceptions
from aiida.orm.nodes.caching import NodeCaching
from aiida.orm.nodes.node import Node


class ContractedNodeCaching(NodeCaching):
    """Disable all caching behavior for contraction markers."""

    def should_use_cache(self) -> bool:
        return False

    @property
    def is_valid_cache(self) -> bool:
        return False

    @is_valid_cache.setter
    def is_valid_cache(self, valid: bool) -> None:
        msg = 'contraction markers cannot be cache sources'
        raise exceptions.ModificationNotAllowed(msg)


class ContractedNode(Node):
    """An immutable marker for a connected region of deleted provenance.

    The class is internal and instances are created exclusively by provenance
    contraction. It intentionally does not derive from :class:`ProcessNode`,
    since it does not represent an execution.
    """

    _CLS_NODE_CACHING = ContractedNodeCaching
    _storable = True
    _cachable = False
    _unstorable_message = 'storing for this node has been disabled'
