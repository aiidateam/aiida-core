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

import six

from aiida.orm.data import BaseType
from aiida.orm.data import to_aiida_type


class Str(BaseType):
    """
    Class to store strings as AiiDA nodes
    """
    _type = str


@to_aiida_type.register(six.string_types[0])
def _(value):
    return Str(value)
