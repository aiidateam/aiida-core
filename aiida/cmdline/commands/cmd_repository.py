# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi repository` command."""
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import decorators, echo


@verdi.group('repository')
def verdi_repo():
    """Manage the AiiDA repository."""


@verdi_repo.command('summary')
@decorators.with_dbenv()
def summary():
    """ """
    from aiida.manage.manager import get_manager
    repository = get_manager().get_profile().get_repository()
    data = {
        "UUID": repository.uuid,
        "objects": repository.count_objects()
    }
    echo.echo_dictionary(data, sort_keys=False, fmt='yaml')


@verdi_repo.command('clean')
@decorators.with_dbenv()
def clean():
    """ """
    from aiida.manage.manager import get_manager
    repository = get_manager().get_profile().get_repository()
    repository.erase()


@verdi_repo.command('other')
@decorators.with_dbenv()
def other():
    """ """
    pass