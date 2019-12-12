# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test module parameter type for click."""
import click


class TestModuleParamType(click.ParamType):
    """Parameter type to represent a unittest module.

    Defunct - remove when removing the "verdi devel tests" command.
    """

    name = 'test module'
