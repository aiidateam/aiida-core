# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The main `verdi` click group."""

from __future__ import absolute_import
import click


@click.group()
@click.option(
    '-p', '--profile', metavar='PROFILE', help='Execute the command for this profile instead of the default profile.')
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
