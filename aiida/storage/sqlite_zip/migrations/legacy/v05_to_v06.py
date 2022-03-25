# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration from v0.5 to v0.6, used by `verdi export migrate` command.

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
from typing import Union

from ..utils import update_metadata, verify_metadata_version  # pylint: disable=no-name-in-module


def migrate_deserialized_datetime(data, conversion):
    """Deserialize datetime strings from export archives, meaning to reattach the UTC timezone information."""
    from aiida.common.exceptions import StorageMigrationError

    ret_data: Union[str, dict, list]

    if isinstance(data, dict):
        ret_data = {}
        for key, value in data.items():
            if conversion is not None:
                ret_data[key] = migrate_deserialized_datetime(value, conversion[key])
            else:
                ret_data[key] = migrate_deserialized_datetime(value, None)
    elif isinstance(data, (list, tuple)):
        ret_data = []
        if conversion is not None:
            for value, sub_conversion in zip(data, conversion):
                ret_data.append(migrate_deserialized_datetime(value, sub_conversion))
        else:
            for value in data:
                ret_data.append(migrate_deserialized_datetime(value, None))
    else:
        if conversion is None:
            ret_data = data
        else:
            if conversion == 'date':
                # Node attributes that were datetime objects were converted to a string since datetimes cannot be stored
                # in JSON. The function used to serialize was:
                # `data.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')
                # Note that this first converted the datetime to UTC but then dropped the information from the string.
                # Since we know that all strings will be UTC, here we are simply reattaching that information.
                ret_data = f'{data}+00:00'
            else:
                raise StorageMigrationError(f"Unknown convert_type '{conversion}'")

    return ret_data


def migration_serialize_datetime_objects(data):
    """Apply migration 0037 - REV. 1.0.37

    Migrates the node `attributes` and `extras` from the EAV schema to JSONB columns. Since JSON does not support
    datetime objects, and the EAV did, existing datetime objects have to be serialized to strings. Just like the
    database migration they were serialized to the standard ISO format, except that they were first converted to UTC
    timezone and then the stored without a timezone reference. Since existing datetimes in the attributes and extras in
    the database were timezone aware and have been migrated to an ISO format string *including* the timezone information
    we should now add the same timezone information to datetime attributes and extras in existing export archives. All
    that one needs to do for this is to append the `+00:00` suffix, which signifies the UTC timezone.

    Since the datetime objects were the only types being serialized in the attributes and extras, after the reinstating
    of the timeonze information, there is no longer a need for the de/serialization dictionaries for each node, stored
    in `node_attributes_conversion` and `node_extras_conversion`, respectively. They are no longer added to new archives
    and so they can and should be removed from existing archives, reducing the size enormously.
    """
    data['node_attributes'] = migrate_deserialized_datetime(data['node_attributes'], data['node_attributes_conversion'])
    data['node_extras'] = migrate_deserialized_datetime(data['node_extras'], data['node_extras_conversion'])

    data.pop('node_attributes_conversion', None)
    data.pop('node_extras_conversion', None)


def migration_migrate_legacy_job_calculation_data(data):
    """Apply migration 0038 - REV. 1.0.38

    Migrates legacy `JobCalculation` data to the new process system. Essentially old `JobCalculation` nodes, which
    have already been migrated to `CalcJobNodes`, are missing important attributes `process_state`, `exit_status` and
    `process_status`. These are inferred from the old `state` attribute, which is then discarded as its values have
    been deprecated.
    """
    from aiida.storage.psql_dos.migrations.utils.calc_state import STATE_MAPPING

    calc_job_node_type = 'process.calculation.calcjob.CalcJobNode.'
    node_data = data['export_data'].get('Node', {})
    calc_jobs = {pk for pk, values in node_data.items() if values['node_type'] == calc_job_node_type}

    for pk in data['node_attributes']:

        # Get a reference to the attributes, so later we update the attribute dictionary in place
        values = data['node_attributes'][pk]

        state = values.get('state', None)

        # Only continue if the pk corresponds to a `CalcJobNode` *and* the `state` is one in the `STATE_MAPPING`
        if pk not in calc_jobs or state not in STATE_MAPPING:
            continue

        # Pop the `state` attribute if it exists, since in any case it will have to be discarded since it is invalid
        state = values.pop('state', None)

        try:
            mapped = STATE_MAPPING[state]
        except KeyError:
            pass
        else:
            # Add the mapped process attributes to the export dictionary if not `None` even if it already exists
            if mapped.exit_status is not None:
                values['exit_status'] = mapped.exit_status
            if mapped.process_state is not None:
                values['process_state'] = mapped.process_state
            if mapped.process_status is not None:
                values['process_status'] = mapped.process_status

            values['process_label'] = 'Legacy JobCalculation'


def migrate_v5_to_v6(metadata: dict, data: dict) -> None:
    """Migration of archive files from v0.5 to v0.6"""
    old_version = '0.5'
    new_version = '0.6'

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    # Apply migrations
    migration_serialize_datetime_objects(data)
    migration_migrate_legacy_job_calculation_data(data)
