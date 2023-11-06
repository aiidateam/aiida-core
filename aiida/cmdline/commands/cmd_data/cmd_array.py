# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data core.array` command."""

from aiida.cmdline.commands.cmd_data import verdi_data
from aiida.cmdline.params import arguments, options, types


@verdi_data.group('core.array')
def array():
    """Manipulate ArrayData objects (numpy arrays)."""


@array.command('show')
@arguments.DATA(type=types.DataParamType(sub_classes=('aiida.data:core.array',)))
@options.DICT_FORMAT()
def array_show(data, fmt):
    """Visualize ArrayData objects."""
    from aiida.cmdline.utils.echo import echo_dictionary

    for node in data:
        the_dict = {}
        for arrayname in node.get_arraynames():
            the_dict[arrayname] = node.get_array(arrayname).tolist()
        echo_dictionary(the_dict, fmt)
