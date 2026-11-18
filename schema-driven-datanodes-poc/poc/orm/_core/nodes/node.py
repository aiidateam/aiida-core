###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A tiny core node object for the PoC."""

from __future__ import annotations

import typing as t


class Node:
    """Minimal base node carrying identity and user-facing metadata."""

    def __init__(self, *, uuid: str = '', label: str = '') -> None:
        self.uuid = uuid
        self.label = label

    def as_dict(self) -> dict[str, t.Any]:
        """Return a plain representation of the base node state."""
        return {'uuid': self.uuid, 'label': self.label}
