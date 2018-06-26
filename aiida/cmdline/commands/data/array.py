# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import click
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands import verdi, verdi_data
from aiida.cmdline.params import arguments
from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.common.exceptions import DanglingLinkError


        
@verdi_data.group('array')
@click.pass_context
def array(ctx):
    """
    Visualize array object
    """
    pass
    

@array.command('show')
@arguments.NODES()
@click.option('-f', '--format', 'format',
              type=click.Choice(['json_date']),
              default='json_date',
              help="Type of the visualization format/tool.")
def show(format, nodes):
    """
    Visualize array object
    """
    from aiida.orm.data.array import ArrayData
    from aiida.cmdline import print_dictionary
    for node in nodes:
        if not isinstance(node, ArrayData):
            echo.echo_critical("Node {} is of class {} instead of {}".format(node, type(node), ArrayData))
        the_dict = {}
        for arrayname in node.arraynames():
            the_dict[arrayname] = node.get_array(arrayname).tolist()
        print_dictionary(the_dict, 'json+date')
