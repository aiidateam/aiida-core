# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration from v0.7 to v0.8, used by `verdi export migrate` command.

The migration steps are named similarly to the database migrations for Django and SQLAlchemy.
In the description of each migration, a revision number is given, which refers to the Django migrations.
The individual Django database migrations may be found at:

    `aiida.storage.djsite.db.migrations.00XX_<migration-name>.py`

Where XX are the numbers in the migrations' documentation: REV. 1.0.XX
And migration-name is the name of the particular migration.
The individual SQLAlchemy database migrations may be found at:

    `aiida.storage.psql_dos.migrations.versions.<id>_<migration-name>.py`

Where id is a SQLA id and migration-name is the name of the particular migration.
"""
# pylint: disable=invalid-name
from ..utils import update_metadata, verify_metadata_version  # pylint: disable=no-name-in-module


def migration_default_link_label(data: dict):
    """Apply migration 0043 - REV. 1.0.43

    Rename all link labels `_return` to `result`.
    """
    for link in data.get('links_uuid', []):
        if link['label'] == '_return':
            link['label'] = 'result'


def migrate_v7_to_v8(metadata: dict, data: dict) -> None:
    """Migration of archive files from v0.7 to v0.8."""
    old_version = '0.7'
    new_version = '0.8'

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    # Apply migrations
    migration_default_link_label(data)
