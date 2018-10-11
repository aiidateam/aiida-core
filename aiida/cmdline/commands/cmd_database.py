# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi database` commands."""
from __future__ import absolute_import

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import echo


@verdi.group('database')
def verdi_database():
    """Inspect and manage the database."""
    pass


@verdi_database.group('integrity')
def verdi_database_integrity():
    """Various commands that will check the integrity of the database and fix potential issues when asked."""
    pass


@verdi_database_integrity.command('duplicate-node-uuid')
@click.option(
    '-a',
    '--apply-patch',
    is_flag=True,
    help='Apply the proposed changes. If this flag is not passed, a dry run is performed instead.')
def database_integrity(apply_patch):
    """Detect and solve nodes with duplicate UUIDs.

    Before aiida-core v1.0.0, there was no uniqueness constraint on the UUID column of the Node table in the database.
    This made it possible to store multiple nodes with identical UUIDs without the database complaining. This was bug
    was fixed in aiida-core=1.0.0 by putting an explicit uniqueness constraint on node UUIDs on the database level.
    However, this would leave databases created before this patch with duplicate UUIDs in an inconsistent state. This
    command will run an analysis to detect duplicate UUIDs in the node table and solve it by generating new UUIDs. Note
    that it will not delete or merge any nodes.
    """
    from aiida.backends import settings
    from aiida.backends.utils import _load_dbenv_noschemacheck
    from aiida.common.setup import get_default_profile_name
    from aiida.manage.database.integrity import deduplicate_node_uuids

    if settings.AIIDADB_PROFILE is not None:
        profile = settings.AIIDADB_PROFILE
    else:
        profile = get_default_profile_name()

    _load_dbenv_noschemacheck(profile)

    try:
        messages = deduplicate_node_uuids(dry_run=not apply_patch)
    except Exception as exception:  # pylint: disable=broad-except
        echo.echo_critical('integrity check failed: {}'.format(str(exception)))
    else:
        for message in messages:
            echo.echo_info(message)

        if apply_patch:
            echo.echo_success('integrity patch completed')
        else:
            echo.echo_success('dry-run of integrity patch completed')
