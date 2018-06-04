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

from aiida.cmdline.utils.pluginable import Pluginable


def click_subcmd_complete(cmd_group):
    """Create a subcommand completion function for a click command group."""
    def complete(subargs_idx, subargs):
        """List valid subcommands for a command group that start with the last subarg."""
        if subargs_idx >= 1:
            return None
        incomplete = subargs[-1]
        print '\n'.join(cmd_group.list_commands({'parameters': [incomplete]}))
    return complete


@click.group()
@click.option('--profile', '-p')
@click.pass_context
def verdi(ctx, profile):
    """
    Toplevel command for click-implemented verdi commands.

    Might eventually replace ``execute_from_cmdline``, however, there is no way to directly call this command from the commandline
    currently. Instead, it is used for subcommand routing of commands written in click, see aiida/cmdline/commands/work.py for an
    example. In short it exists, so the name by which the subcommand is called ('verdi something something') matches it's command
    group hierarchy (group ``verdi``, subgroup ``something``, command ``something``).

    """
    ctx.obj = {'profile': profile}


@verdi.command()
@click.argument('completion_args', nargs=-1, type=click.UNPROCESSED)
def completion(completion_args):
    """
    Completion command alias for click-implemented verdi commands.

    Due to the roundabout process by which click-implemented verdi commands are called, pressing <Tab><Tab> on one of them tries to
    call aiida.cmdline.commands.verdi with subcommand completion. Therefore in order to enable the same behaviour as on older commands,
    such a subcommand with the same signature must exist and must run the same code with the same arguments.
    """
    from aiida.cmdline.verdilib import Completion
    Completion().run(*completion_args)


@verdi.group('calculation')
def verdi_calculation():
    pass

@verdi.group('code')
def verdi_code():
    pass

@verdi.group('comment')
def verdi_comment():
    pass

@verdi.group('computer')
def verdi_computer():
    pass

@verdi.group('daemon')
def verdi_daemon():
    pass

@verdi.group('data', entry_point_group='aiida.cmdline.data', cls=Pluginable)
def verdi_data():
    """Verdi data interface for plugin commands."""
    pass

@verdi.group('devel')
def verdi_devel():
    pass

@verdi.group('export')
def verdi_export():
    pass

@verdi.group('graph')
def verdi_graph():
    pass

@verdi.group('group')
def verdi_group():
    pass

@verdi.group('import')
def verdi_import():
    pass

@verdi.group('node')
def verdi_node():
    pass

@verdi.group('profile')
def verdi_profile():
    pass

@verdi.group('rehash')
def verdi_rehash():
    pass

@verdi.group('restapi')
def verdi_restapi():
    pass

@verdi.group('shell')
def verdi_shell():
    pass

@verdi.group('user')
def verdi_user():
    pass

@verdi.group('work')
def verdi_work():
    pass
