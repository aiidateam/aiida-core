# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration from v0.4 to v0.5, used by `verdi export migrate` command.

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

from aiida.tools.importexport.migration.utils import verify_metadata_version, update_metadata, remove_fields


def migration_drop_node_columns_nodeversion_public(metadata, data):
    """Apply migration 0034 - REV. 1.0.34
    Drop the columns `nodeversion` and `public` from the `Node` model
    """
    entity = 'Node'
    fields = ['nodeversion', 'public']

    remove_fields(metadata, data, [entity], fields)


def migration_drop_computer_transport_params(metadata, data):
    """Apply migration 0036 - REV. 1.0.36
    Drop the column `transport_params` from the `Computer` model
    """
    entity = 'Computer'
    field = 'transport_params'

    remove_fields(metadata, data, [entity], [field])


def migrate_v4_to_v5(metadata, data, *args):  # pylint: disable=unused-argument
    """
    Migration of export files from v0.4 to v0.5

    This is from migration 0034 (drop_node_columns_nodeversion_public) and onwards
    """
    old_version = '0.4'
    new_version = '0.5'

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    # Apply migrations
    migration_drop_node_columns_nodeversion_public(metadata, data)
    migration_drop_computer_transport_params(metadata, data)
