# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This allows to manage ParameterData objects from command line.
"""
from aiida.cmdline.commands.cmd_data import verdi_data
from aiida.cmdline.params import arguments
from aiida.cmdline.utils import echo


@verdi_data.group('parameter')
def parameter():
    """
    View and manipulate Parameter data classes.
    """
    pass


@parameter.command('show')
@arguments.NODES()
def show(nodes):
    """
    Show contents of ParameterData nodes.
    """
    from aiida.orm.data.parameter import ParameterData
    from aiida.cmdline.utils.echo import echo_dictionary
    for node in nodes:
        if not isinstance(node, ParameterData):
            echo.echo_error("Node {} is of class {} instead of {}".format(node, type(node), ParameterData))
            continue
        the_dict = node.get_dict()
        echo_dictionary(the_dict, 'json+date')
