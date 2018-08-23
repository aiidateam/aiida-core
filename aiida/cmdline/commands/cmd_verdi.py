# -*- coding: utf-8 -*-
"""The main `verdi` click group."""

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
