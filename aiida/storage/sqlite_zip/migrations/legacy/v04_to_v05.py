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

    `aiida.storage.djsite.db.migrations.00XX_<migration-name>.py`

Where XX are the numbers in the migrations' documentation: REV. 1.0.XX
And migration-name is the name of the particular migration.
The individual SQLAlchemy database migrations may be found at:

    `aiida.storage.psql_dos.migrations.versions.<id>_<migration-name>.py`

Where id is a SQLA id and migration-name is the name of the particular migration.
"""
# pylint: disable=invalid-name
from ..utils import update_metadata, verify_metadata_version  # pylint: disable=no-name-in-module


def remove_fields(metadata, data, entities, fields):
    """Remove fields under entities from data.json and metadata.json.

    :param metadata: the content of an export archive metadata.json file
    :param data: the content of an export archive data.json file
    :param entities: list of ORM entities
    :param fields: list of fields to be removed from the export archive files
    """
    # data.json
    for entity in entities:
        for content in data['export_data'].get(entity, {}).values():
            for field in fields:
                content.pop(field, None)

    # metadata.json
    for entity in entities:
        for field in fields:
            metadata['all_fields_info'][entity].pop(field, None)


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


def migrate_v4_to_v5(metadata: dict, data: dict) -> None:
    """
    Migration of archive files from v0.4 to v0.5

    This is from migration 0034 (drop_node_columns_nodeversion_public) and onwards
    """
    old_version = '0.4'
    new_version = '0.5'

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    # Apply migrations
    migration_drop_node_columns_nodeversion_public(metadata, data)
    migration_drop_computer_transport_params(metadata, data)
