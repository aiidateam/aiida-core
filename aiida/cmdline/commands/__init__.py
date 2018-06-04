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
    ctx.help_option_names = ['-h', '--help']


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
@click.pass_context
def verdi_calculation(ctx):
    pass

@verdi.group('code')
@click.pass_context
def verdi_code(ctx):
    pass

@verdi.group('comment')
@click.pass_context
def verdi_comment(ctx):
    pass

@verdi.group('computer')
@click.pass_context
def verdi_computer(ctx):
    pass

@verdi.group('daemon')
@click.pass_context
def verdi_daemon(ctx):
    pass

@verdi.group('data', entry_point_group='aiida.cmdline.data', cls=Pluginable)
@click.pass_context
def verdi_data(ctx):
    """Verdi data interface for plugin commands."""
    pass

@verdi.group('devel')
@click.pass_context
def verdi_devel(ctx):
    pass

@verdi.group('export')
@click.pass_context
def verdi_export(ctx):
    pass

@verdi.group('graph')
@click.pass_context
def verdi_graph(ctx):
    pass

@verdi.group('group')
@click.pass_context
def verdi_group(ctx):
    pass

@verdi.group('import')
@click.pass_context
def verdi_import(ctx):
    pass

@verdi.group('node')
@click.pass_context
def verdi_node(ctx):
    pass

@verdi.group('profile')
@click.pass_context
def verdi_profile(ctx):
    pass

@verdi.group('rehash')
@click.pass_context
def verdi_rehash(ctx):
    pass

@verdi.group('restapi')
@click.pass_context
def verdi_restapi(ctx):
    pass

@verdi.group('shell')
@click.pass_context
def verdi_shell(ctx):
    pass

@verdi.group('user')
@click.pass_context
def verdi_user(ctx):
    pass

@verdi.group('work')
@click.pass_context
def verdi_work(ctx):
    pass
