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
from click_plugins import with_plugins


def click_subcmd_complete(cmd_group):
    def complete(subargs_idx, subargs):
        if subargs_idx >= 1:
            return None
        incomplete = subargs[-1]
        print '\n'.join(cmd_group.list_commands({'parameters': [incomplete]}))
    return complete


@click.group()
@click.option('--profile', '-p')
def verdi(profile):
    pass


@verdi.command()
@click.argument('completion_args', nargs=-1, type=click.UNPROCESSED)
def completion(completion_args):
    from aiida.cmdline.verdilib import Completion
    Completion().run(*completion_args)


@verdi.group()
def export():
    pass


@verdi.group()
def work():
    pass

@verdi.group()
def user():
    pass


@verdi.group('data')
def data_cmd():
    pass
