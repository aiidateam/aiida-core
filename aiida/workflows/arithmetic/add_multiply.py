# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# start-marker for docs
"""Basic calcfunction-based workflows for demonstration purposes."""
from aiida.engine import calcfunction, workfunction


@calcfunction
def add(x, y):
    return x + y


@calcfunction
def multiply(x, y):
    return x * y


@workfunction
def add_multiply(x, y, z):
    """Add two numbers and multiply it with a third."""
    addition = add(x, y)
    product = multiply(addition, z)
    return product
