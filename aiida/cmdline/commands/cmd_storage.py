# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi storage` commands."""

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.common import exceptions


@verdi.group('storage')
def verdi_database():
    """Inspect and manage the internal storage."""


@verdi_database.command('migrate')
@options.FORCE()
def backend_migrate(force):
    """Migrate the database to the latest schema version."""
    from aiida.engine.daemon.client import get_daemon_client
    from aiida.manage.manager import get_manager

    client = get_daemon_client()
    if client.is_daemon_running:
        echo.echo_critical('Migration aborted, the daemon for the profile is still running.')

    manager = get_manager()
    profile = manager.get_profile()
    backend = manager._load_backend(schema_check=False)  # pylint: disable=protected-access

    if force:
        try:
            backend.migrate()
        except (exceptions.ConfigurationError, exceptions.DatabaseMigrationError) as exception:
            echo.echo_critical(str(exception))
        return

    echo.echo_warning('Migrating your database might take a while and is not reversible.')
    echo.echo_warning('Before continuing, make sure you have completed the following steps:')
    echo.echo_warning('')
    echo.echo_warning(' 1. Make sure you have no active calculations and workflows.')
    echo.echo_warning(' 2. If you do, revert the code to the previous version and finish running them first.')
    echo.echo_warning(' 3. Stop the daemon using `verdi daemon stop`')
    echo.echo_warning(' 4. Make a backup of your database and repository')
    echo.echo_warning('')
    echo.echo_warning('', nl=False)

    expected_answer = 'MIGRATE NOW'
    confirm_message = 'If you have completed the steps above and want to migrate profile "{}", type {}'.format(
        profile.name, expected_answer
    )

    try:
        response = click.prompt(confirm_message)
        while response != expected_answer:
            response = click.prompt(confirm_message)
    except click.Abort:
        echo.echo('\n')
        echo.echo_critical('Migration aborted, the data has not been affected.')
    else:
        try:
            backend.migrate()
        except (exceptions.ConfigurationError, exceptions.DatabaseMigrationError) as exception:
            echo.echo_critical(str(exception))
        else:
            echo.echo_success('migration completed')


@verdi_database.group('integrity')
def verdi_database_integrity():
    """Checks for the integrity of the database and the repository."""


@verdi_database.command('info')
@click.option('--statistics', is_flag=True, help='Provides more in-detail statistically relevant data.')
def storage_info(statistics):
    """Summarise the contents of the storage."""
    from aiida.orm import Comment, Computer, Group, Log, Node, QueryBuilder, User
    data = {}

    # User
    query_user = QueryBuilder().append(User, project=['email'])
    data['Users'] = {'count': query_user.count()}
    if statistics:
        data['Users']['emails'] = query_user.distinct().all(flat=True)

    # Computer
    query_comp = QueryBuilder().append(Computer, project=['label'])
    data['Computers'] = {'count': query_comp.count()}
    if statistics:
        data['Computers']['labels'] = query_comp.distinct().all(flat=True)

    # Node
    count = QueryBuilder().append(Node).count()
    data['Nodes'] = {'count': count}
    if statistics:
        node_types = QueryBuilder().append(Node, project=['node_type']).distinct().all(flat=True)
        data['Nodes']['node_types'] = node_types
        process_types = QueryBuilder().append(Node, project=['process_type']).distinct().all(flat=True)
        data['Nodes']['process_types'] = [p for p in process_types if p]

    # Group
    query_group = QueryBuilder().append(Group, project=['type_string'])
    data['Groups'] = {'count': query_group.count()}
    if statistics:
        data['Groups']['type_strings'] = query_group.distinct().all(flat=True)

    # Comment
    count = QueryBuilder().append(Comment).count()
    data['Comments'] = {'count': count}

    # Log
    count = QueryBuilder().append(Log).count()
    data['Logs'] = {'count': count}

    echo.echo_dictionary(data, sort_keys=False, fmt='yaml')
