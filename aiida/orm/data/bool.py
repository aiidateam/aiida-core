# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
import numpy
from aiida.orm.data import BaseType
from aiida.orm.data import to_aiida_type


class Bool(BaseType):
    """
    Class to store booleans as AiiDA nodes
    """
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
    """
    Return a Bool Data node, with value True

    Cannot be done as a singleton in the module, because it would be generated
    at import time, with the risk that (e.g. in the tests, or at the very first use
    of AiiDA) a user is not yet defined in the DB (but a user is mandatory in the
    DB before you can create new Nodes in AiiDA).
    """
    TRUE = Bool(typevalue=(bool, True))
    return TRUE


def get_false_node():
    """
    Return a Bool Data node, with value False

    Cannot be done as a singleton in the module, because it would be generated
    at import time, with the risk that (e.g. in the tests, or at the very first use
    of AiiDA) a user is not yet defined in the DB (but a user is mandatory in the
    DB before you can create new Nodes in AiiDA).
    """
    FALSE = Bool(typevalue=(bool, False))
    return FALSE
