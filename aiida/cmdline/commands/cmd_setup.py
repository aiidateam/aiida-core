# -*- coding: utf-8 -*-
# pylint: disable=too-many-arguments
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi setup` command."""
import click

from aiida.cmdline.commands import verdi
from aiida.control.profile import setup_profile


@verdi.command('setup')
@click.argument('profile', default='', type=str)
@click.option('--only-config', is_flag=True)
@click.option('--non-interactive', is_flag=True, help='never prompt the user for input, read values from options')
@click.option(
    '--backend',
    type=click.Choice(['django', 'sqlalchemy']),
)
@click.option('--email', type=str)
@click.option('--db_host', type=str)
@click.option('--db_port', type=int)
@click.option('--db_name', type=str)
@click.option('--db_user', type=str)
@click.option('--db_pass', type=str)
@click.option('--first-name', type=str)
@click.option('--last-name', type=str)
@click.option('--institution', type=str)
@click.option('--repo', type=str)
def setup(profile, only_config, non_interactive, backend, email, db_host, db_port, db_name, db_user, db_pass,
          first_name, last_name, institution, repo):
    """Setup and configure a new profile."""
    kwargs = dict(
        profile=profile,
        only_config=only_config,
        non_interactive=non_interactive,
        backend=backend,
        email=email,
        db_host=db_host,
        db_port=db_port,
        db_name=db_name,
        db_user=db_user,
        db_pass=db_pass,
        first_name=first_name,
        last_name=last_name,
        institution=institution,
        repo=repo)
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    setup_profile(**kwargs)
