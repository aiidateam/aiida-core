# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a string value."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from .base import BaseType, to_aiida_type

__all__ = ('Str',)


class Str(BaseType):
    """`Data` sub class to represent a string value."""

    _type = str


@to_aiida_type.register(six.string_types[0])
def _(value):
    return Str(value)
