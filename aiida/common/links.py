# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to define valid link types."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from enum import Enum

__all__ = ('LinkType',)


class LinkType(Enum):
    """A simple enum of allowed link types."""

    CREATE = 'create'
    RETURN = 'return'
    INPUT_CALC = 'input_calc'
    INPUT_WORK = 'input_work'
    CALL_CALC = 'call_calc'
    CALL_WORK = 'call_work'
