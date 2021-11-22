# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data dict` command."""

from aiida.cmdline.commands.cmd_data import verdi_data
from aiida.cmdline.params import arguments, options, types


@verdi_data.group('dict')
def dictionary():
    """Manipulate Dict objects (python dictionaries)."""


@dictionary.command('show')
@arguments.DATA(type=types.DataParamType(sub_classes=('aiida.data:core.dict',)))
@options.DICT_FORMAT()
def dictionary_show(data, fmt):
    """Show contents of Dict nodes."""
    from aiida.cmdline.utils.echo import echo_dictionary

    for node in data:
        echo_dictionary(node.get_dict(), fmt)
