###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Process node representing provenance that was intentionally removed."""

from __future__ import annotations

from .process import ProcessNode

__all__ = ('ContractedProcessNode',)


class ContractedProcessNode(ProcessNode):
    """An immutable marker for a connected region of deleted provenance.

    This node does not represent an executable process and can never be used as
    a cache source. Instances are created exclusively by replacement deletion.
    """

    _storable = True
    _cachable = False
    _unstorable_message = 'storing for this node has been disabled'
