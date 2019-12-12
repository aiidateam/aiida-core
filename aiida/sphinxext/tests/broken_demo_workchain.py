# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""This module defines a broken example workchain for testing that errors are not swallowed."""

from aiida.engine import WorkChain


class BrokenDemoWorkChain(WorkChain):
    """
    A demo workchain that raises when its spec is built.
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)
        raise ValueError('The broken workchain says hi!')
