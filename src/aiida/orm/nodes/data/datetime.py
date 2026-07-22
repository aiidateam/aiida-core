###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a :class:`datetime.datetime` value."""

from __future__ import annotations

import datetime

from .base import to_aiida_type
from .data import Data

__all__ = ('DateTimeData',)


@to_aiida_type.register(datetime.datetime)
def _(value):
    return DateTimeData(value)


class DateTimeData(Data):
    """`Data` sub class to store a :class:`datetime.datetime` object.

    The value is stored as an ISO-8601 string for portability across backends and reconstructed on access.
    """

    def __init__(self, value, **kwargs):
        if not isinstance(value, datetime.datetime):
            msg = f'expected a datetime.datetime, got {type(value)}'
            raise TypeError(msg)
        super().__init__(**kwargs)
        self.base.attributes.set('datetime', value.isoformat())

    @property
    def value(self) -> datetime.datetime:
        """Return the stored value as a :class:`datetime.datetime`."""
        return datetime.datetime.fromisoformat(self.base.attributes.get('datetime'))

    def __str__(self) -> str:
        return str(self.value)
