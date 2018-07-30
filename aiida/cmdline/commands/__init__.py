# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=cyclic-import
"""The `verdi` command line interface."""
import click
import click_completion

# Activate the completion of parameter types provided by the click_completion package
click_completion.init()


@click.group(invoke_without_command=True)
@click.option('-p', '--profile', help='Execute the command for this profile instead of the default profile.')
@click.option('--version', is_flag=True, default=False, help='Print the version of AiiDA that is currently installed.')
@click.pass_context
def verdi(ctx, profile, version):
    """The command line interface of AiiDA."""
    import sys
    import aiida
    from aiida.cmdline.utils import echo

    if version:
        echo.echo('AiiDA version {}'.format(aiida.__version__))
        sys.exit(0)

    if profile is not None:
        from aiida.backends import settings
        settings.AIIDADB_PROFILE = profile

    ctx.help_option_names = ['-h', '--help']


# Import to populate the `verdi` sub commands
# pylint: disable=wrong-import-position
from aiida.cmdline.commands import (cmd_calculation, cmd_code, cmd_comment, cmd_computer, cmd_data, cmd_daemon,
                                    cmd_devel, cmd_export, cmd_graph, cmd_group, cmd_import, cmd_node, cmd_profile,
                                    cmd_quicksetup, cmd_rehash, cmd_restapi, cmd_run, cmd_setup, cmd_shell, cmd_user,
                                    cmd_work, cmd_workflow)

# Import to populate the `verdi data` sub commands
# pylint: disable=wrong-import-position
from aiida.cmdline.commands.cmd_data import (cmd_array, cmd_bands, cmd_cif, cmd_parameter, cmd_remote, cmd_structure,
                                             cmd_trajectory, cmd_upf)
