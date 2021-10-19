# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data singlefile` command."""

from aiida.cmdline.commands.cmd_data import verdi_data
from aiida.cmdline.params import arguments, types
from aiida.cmdline.utils import decorators, echo


@verdi_data.group('singlefile')
def singlefile():
    """Work with SinglefileData nodes."""


@singlefile.command('content')
@arguments.DATUM(type=types.DataParamType(sub_classes=('aiida.data:core.singlefile',)))
@decorators.with_dbenv()
def singlefile_content(datum):
    """Show the content of the file."""
    try:
        echo.echo(datum.get_content())
    except (IOError, OSError) as exception:
        echo.echo_critical(f'could not read the content for SinglefileData<{datum.pk}>: {str(exception)}')
