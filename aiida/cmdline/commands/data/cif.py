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
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.cmdline.commands.data.list import _list
from aiida.orm.data.cif import CifData
from aiida.cmdline.commands.data.list import list_options


@verdi_data.group('cif')
@click.pass_context
def cif(ctx):
    """help"""
    pass
    

@cif.command('list')
@list_options
def list_cif(elements, elements_only, formulamode, past_days, groups, all_users):
    """
    List stored BandData objects
    """
    project = ['ID', 'Ctime', 'Label', 'Formula']
    _list(CifData, project, elements, elements_only, formulamode, past_days, groups, all_users)



@cif.command()
def show():
    """help"""
    click.echo("Test")
