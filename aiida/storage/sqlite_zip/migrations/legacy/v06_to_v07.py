# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration from v0.6 to v0.7, used by `verdi export migrate` command.

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


def data_migration_legacy_process_attributes(data):
    """Apply migration 0040 - REV. 1.0.40
    Data migration for some legacy process attributes.

    Attribute keys that are renamed:

    * `_sealed` -> `sealed`

    Attribute keys that are removed entirely:

    * `_finished`
    * `_failed`
    * `_aborted`
    * `_do_abort`

    Finally, after these first migrations, any remaining process nodes are screened for the existence of the
    `process_state` attribute. If they have it, it is checked whether the state is active or not, if not, the `sealed`
    attribute is created and set to `True`.

    :raises `~aiida.common.exceptions.CorruptStorage`: if a Node, found to have attributes,
        cannot be found in the list of exported entities.
    :raises `~aiida.common.exceptions.CorruptStorage`: if the 'sealed' attribute does not exist and
        the ProcessNode is in an active state, i.e. `process_state` is one of ('created', 'running', 'waiting').
        A log-file, listing all illegal ProcessNodes, will be produced in the current directory.
    """
    from aiida.common.exceptions import CorruptStorage
    from aiida.storage.psql_dos.migrations.utils.integrity import write_database_integrity_violation

    attrs_to_remove = ['_sealed', '_finished', '_failed', '_aborted', '_do_abort']
    active_states = {'created', 'running', 'waiting'}
    illegal_cases = []

    for node_pk, content in data['node_attributes'].items():
        try:
            if data['export_data']['Node'][node_pk]['node_type'].startswith('process.'):
                # Check if the ProcessNode has a 'process_state' attribute, and if it's non-active.
                # Raise if the ProcessNode is in an active state, otherwise set `'sealed' = True`
                process_state = content.get('process_state', '')
                if process_state in active_states:
                    # The ProcessNode is in an active state, and should therefore never have been allowed
                    # to be exported. The Node will be added to a log that is saved in the working directory,
                    # then a CorruptStorage will be raised, since the archive needs to be migrated manually.
                    uuid_pk = data['export_data']['Node'][node_pk].get('uuid', node_pk)
                    illegal_cases.append([uuid_pk, process_state])
                    continue  # No reason to do more now

                # Either the ProcessNode is in a non-active state or its 'process_state' hasn't been set.
                # In both cases we claim the ProcessNode 'sealed' and make it importable.
                content['sealed'] = True

                # Remove attributes
                for attr in attrs_to_remove:
                    content.pop(attr, None)
        except KeyError as exc:
            raise CorruptStorage(f'Your export archive is corrupt! Org. exception: {exc}')

    if illegal_cases:
        headers = ['UUID/PK', 'process_state']
        warning_message = 'Found ProcessNodes with active process states ' \
                          'that should never have been allowed to be exported.'
        write_database_integrity_violation(illegal_cases, headers, warning_message)

        raise CorruptStorage(
            'Your export archive is corrupt! '
            'Please see the log-file in your current directory for more details.'
        )


def remove_attribute_link_metadata(metadata):
    """Remove Attribute and Link from metadata.json
    This is not a database migration, but purely to do with the import/export schema.

    The "entities" ATTRIBUTE_ENTITY_NAME and LINK_ENTITY_NAME were introduced in v0.3 or v0.4 of the
    import/export schema. However, they were never used - or the usage has been reverted.
    They will be removed from metadata.json, slightly simplifying the import functions as well.
    """
    entities = {'Attribute', 'Link'}
    dictionaries = {'unique_identifiers', 'all_fields_info'}

    for entity in entities:
        for dictionary in dictionaries:
            metadata[dictionary].pop(entity, None)


def migrate_v6_to_v7(metadata: dict, data: dict) -> None:
    """Migration of archive files from v0.6 to v0.7"""
    old_version = '0.6'
    new_version = '0.7'

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    # Apply migrations
    data_migration_legacy_process_attributes(data)
    remove_attribute_link_metadata(metadata)
