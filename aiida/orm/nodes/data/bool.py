# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a boolean value."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import numpy

from .base import BaseType, to_aiida_type

__all__ = ('Bool',)


class Bool(BaseType):
    """`Data` sub class to represent a boolean value."""

    _type = bool

    def __int__(self):
        return int(bool(self))

    # Python 2
    def __nonzero__(self):
        return self.__bool__()

    # Python 3
    def __bool__(self):
        return self.value


@to_aiida_type.register(bool)
@to_aiida_type.register(numpy.bool_)
def _(value):
    return Bool(value)


def get_true_node():
    """Return a `Bool` node with value `True`

    .. note:: this function serves as a substitute for defining the node as a module singleton, because that would be
        instantiated at import time, at which time not all required database resources may be defined.

    :return: a `Bool` instance with the value `True`
    """
    return Bool(True)


def get_false_node():
    """Return a `Bool` node with value `False`

    .. note:: this function serves as a substitute for defining the node as a module singleton, because that would be
        instantiated at import time, at which time not all required database resources may be defined.

    :return: a `Bool` instance with the value `False`
    """
    return Bool(False)
