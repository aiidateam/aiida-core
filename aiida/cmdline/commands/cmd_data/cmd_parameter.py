# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data parameter` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.cmdline.commands.cmd_data import verdi_data
from aiida.cmdline.params import arguments, types


@verdi_data.group('parameter')
def parameter():
    """View and manipulate Dict objects."""


@parameter.command('show')
@arguments.DATA(type=types.DataParamType(sub_classes=('aiida.data:dict',)))
def parameter_show(data):
    """Show contents of Dict nodes."""
    from aiida.cmdline.utils.echo import echo_dictionary

    for node in data:
        the_dict = node.get_dict()
        echo_dictionary(the_dict, 'json+date')
