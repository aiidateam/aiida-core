# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Module for the non empty string parameter type
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from click.types import StringParamType


class NonEmptyStringParamType(StringParamType):
    """
    Parameter that cannot be an an empty string.
    """
    name = 'nonemptystring'

    def convert(self, value, param, ctx):
        newval = super(NonEmptyStringParamType, self).convert(value, param, ctx)
        if not newval:  # None or empty string
            self.fail("Empty string is not valid!")

        return newval

    def __repr__(self):
        return 'NONEMPTYSTRING'
