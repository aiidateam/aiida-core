###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The `verdi data` command line interface."""

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils.pluginable import Pluginable
from aiida.cmdline.params import arguments, options, types


@verdi.group('data', entry_point_group='aiida.cmdline.data', cls=Pluginable)
def verdi_data():
    """Inspect, create and manage data nodes."""

@verdi_data.command('dump')
@arguments.DATA()
@options.PATH()
@options.OVERWRITE()
# @options. file format
def data_dump(
    data,
    path,
    overwrite,
) -> None:

    """Dump an arbitrary `Data` node entity to disk.

    """
    from aiida.tools.dumping.data import DataDumper

    data_dumper = DataDumper(
        overwrite=overwrite
    )

    print(type(data), data)
    # `data` comes as a tuple
    if len(data) > 1:
        raise NotImplementedError("Dumping of multiple data nodes not yet supported.")

    # Probs shouldn't do that. Quick hack.
    data=data[0]

    data_dumper.dump_rich(data_node=data, output_path=path)
