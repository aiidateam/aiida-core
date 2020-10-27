# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration from v0.0 to v0.10, used by `verdi export migrate` command.

The migration steps are named similarly to the database migrations for Django and SQLAlchemy.
In the description of each migration, a revision number is given, which refers to the Django migrations.
The individual Django database migrations may be found at:

    `aiida.backends.djsite.db.migrations.00XX_<migration-name>.py`

Where XX are the numbers in the migrations' documentation: REV. 1.0.XX
And migration-name is the name of the particular migration.
The individual SQLAlchemy database migrations may be found at:

    `aiida.backends.sqlalchemy.migrations.versions.<id>_<migration-name>.py`

Where id is a SQLA id and migration-name is the name of the particular migration.
"""
# pylint: disable=invalid-name

from aiida.tools.importexport.migration.utils import verify_metadata_version, update_metadata


def migration_add_group_extras(data):
    """Apply migration 0045 - REV. 1.0.45

    Add `extras` column to `Group` instances.
    """
    data['group_extras'] = {}


def migrate_v9_to_v10(metadata, data, *args):  # pylint: disable=unused-argument
    """Migration of archive files from v0.9 to v0.10."""
    old_version = '0.9'
    new_version = '0.10'

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    # Apply migrations
    migration_add_group_extras(data)
