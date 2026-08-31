###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to explicitly represent a Python ``None``."""

from __future__ import annotations

from .base import to_aiida_type
from .data import Data

__all__ = ('NoneData',)


@to_aiida_type.register(type(None))
def _(value):
    return NoneData()


class NoneData(Data):
    """A ``Data`` node that explicitly represents a Python ``None``.

    It carries no repository content and no attributes, so every instance has an identical content hash. That is the
    intended behaviour: ``None`` is a single value. A dedicated node type is needed because ``None`` cannot be stored as
    one of the simple ``BaseType`` nodes (``Int``, ``Bool``, ...), yet a serialized value must always map to a node.
    """

    @property
    def value(self) -> None:
        """Return the represented value, which is always ``None``."""
        return None

    @property
    def obj(self) -> None:
        """Alias of :attr:`value`, mirroring the ``.obj`` accessor of other wrapping data types."""
        return None

    def __repr__(self) -> str:
        return 'NoneData()'

    def __str__(self) -> str:
        return 'NoneData()'
