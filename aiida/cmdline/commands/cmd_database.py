# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi database` commands."""
# pylint: disable=unused-argument

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.utils import decorators


@verdi.group('database', hidden=True)
def verdi_database():
    """Inspect and manage the database.

    .. deprecated:: v2.0.0
    """


@verdi_database.command('version')
@decorators.deprecated_command(
    'This command has been deprecated and no longer has any effect. It will be removed soon from the CLI (in v2.1).\n'
    'The same information is now available through `verdi storage version`.\n'
)
def database_version():
    """Show the version of the database.

    The database version is defined by the tuple of the schema generation and schema revision.

    .. deprecated:: v2.0.0
    """


@verdi_database.command('migrate')
@options.FORCE()
@click.pass_context
@decorators.deprecated_command(
    'This command has been deprecated and will be removed soon (in v3.0). '
    'Please call `verdi storage migrate` instead.\n'
)
def database_migrate(ctx, force):
    """Migrate the database to the latest schema version.

    .. deprecated:: v2.0.0
    """
    from aiida.cmdline.commands.cmd_storage import storage_migrate
    ctx.forward(storage_migrate)


@verdi_database.group('integrity')
def verdi_database_integrity():
    """Check the integrity of the database and fix potential issues.

    .. deprecated:: v2.0.0
    """


@verdi_database_integrity.command('detect-duplicate-uuid')
@click.option(
    '-t',
    '--table',
    default='db_dbnode',
    type=click.Choice(('db_dbcomment', 'db_dbcomputer', 'db_dbgroup', 'db_dbnode')),
    help='The database table to operate on.'
)
@click.option(
    '-a', '--apply-patch', is_flag=True, help='Actually apply the proposed changes instead of performing a dry run.'
)
@decorators.deprecated_command(
    'This command has been deprecated and no longer has any effect. It will be removed soon from the CLI (in v2.1).\n'
    'For remaining available integrity checks, use `verdi storage integrity` instead.\n'
)
def detect_duplicate_uuid(table, apply_patch):
    """Detect and fix entities with duplicate UUIDs.

    Before aiida-core v1.0.0, there was no uniqueness constraint on the UUID column of the node table in the database
    and a few other tables as well. This made it possible to store multiple entities with identical UUIDs in the same
    table without the database complaining. This bug was fixed in aiida-core=1.0.0 by putting an explicit uniqueness
    constraint on UUIDs on the database level. However, this would leave databases created before this patch with
    duplicate UUIDs in an inconsistent state. This command will run an analysis to detect duplicate UUIDs in a given
    table and solve it by generating new UUIDs. Note that it will not delete or merge any rows.


    .. deprecated:: v2.0.0
    """


@verdi_database_integrity.command('detect-invalid-links')
@decorators.with_dbenv()
@decorators.deprecated_command(
    'This command has been deprecated and no longer has any effect. It will be removed soon from the CLI (in v2.1).\n'
    'For remaining available integrity checks, use `verdi storage integrity` instead.\n'
)
def detect_invalid_links():
    """Scan the database for invalid links.

    .. deprecated:: v2.0.0
    """


@verdi_database_integrity.command('detect-invalid-nodes')
@decorators.with_dbenv()
@decorators.deprecated_command(
    'This command has been deprecated and no longer has any effect. It will be removed soon from the CLI (in v2.1).\n'
    'For remaining available integrity checks, use `verdi storage integrity` instead.\n'
)
def detect_invalid_nodes():
    """Scan the database for invalid nodes.

    .. deprecated:: v2.0.0
    """


@verdi_database.command('summary')
@decorators.deprecated_command(
    'This command has been deprecated and no longer has any effect. It will be removed soon from the CLI (in v2.1).\n'
    'Please call `verdi storage info` instead.\n'
)
def database_summary():
    """Summarise the entities in the database.

    .. deprecated:: v2.0.0
    """
