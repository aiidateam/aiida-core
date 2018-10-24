# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Click parameter types for paths."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import os
import click


class AbsolutePathParamType(click.Path):
    """
    The ParamType for identifying absolute Paths (derived from click.Path).
    """

    name = 'AbsolutePath'

    def convert(self, value, param, ctx):
        value = os.path.expanduser(value)
        newval = super(AbsolutePathParamType, self).convert(value, param, ctx)
        if not os.path.isabs(newval):
            raise click.BadParameter('path must be absolute')
        return newval

    def __repr__(self):
        return 'ABSOLUTEPATH'
