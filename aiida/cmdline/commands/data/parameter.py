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
from aiida.cmdline.commands import verdi_data
from aiida.cmdline.params import arguments
from aiida.cmdline.utils import echo

        
@verdi_data.group('parameter')
@click.pass_context
def parameter(ctx):
    """
    View and manipulate Parameter data classes.
    """
    pass
    

@parameter.command('show')
@arguments.NODES()
@click.option('-f', '--format', 'format',
              type=click.Choice(['json_date']),
              default='json_date',
              help="Filter the families only to those containing "
              "a pseudo for each of the specified elements")
def show(nodes, format):
    """
    Show contents of ParameterData nodes.
    """
    from aiida.orm.data.parameter import ParameterData
    from aiida.cmdline import print_dictionary
    for node in nodes:
        if not isinstance(node, ParameterData):
            echo.echo_error("Node {} is of class {} instead of {}".format(node, type(node), ParameterData))
            continue
        the_dict = node.get_dict()
        print_dictionary(the_dict, 'json+date')
