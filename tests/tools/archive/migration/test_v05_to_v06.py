###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test archive file migration from export version 0.5 to 0.6"""

from aiida.storage.psql_dos.migrations.utils.calc_state import STATE_MAPPING
from aiida.storage.sqlite_zip.migrations.legacy import migrate_v5_to_v6  # type: ignore[attr-defined]
from aiida.storage.sqlite_zip.migrations.utils import verify_metadata_version
from tests.utils.archives import get_archive_file, read_json_files


def test_migrate_external(migrate_from_func):
    """Test the migration on the test archive provided by the external test package."""
    _, data = migrate_from_func('export_v0.5_manual.aiida', '0.5', '0.6', migrate_v5_to_v6)

    # Explicitly check that conversion dictionaries were removed
    illegal_data_dicts = {'node_attributes_conversion', 'node_extras_conversion'}
    for dict_ in illegal_data_dicts:
        assert dict_ not in data, f"dictionary '{dict_}' should have been removed from data.json"


def test_migrate_v5_to_v6_calc_states(core_archive, migrate_from_func):
    """Test the data migration of legacy `JobCalcState` attributes.

    This test has to use a local archive because the current archive from the `aiida-export-migration-tests`
    module does not include a `CalcJobNode` with a legacy `state` attribute.
    """
    # Get metadata.json and data.json as dicts from v0.5 file archive
    archive_path = get_archive_file('export_0.5_simple.aiida', **core_archive)
    metadata, data = read_json_files(archive_path)

    verify_metadata_version(metadata, version='0.5')

    calc_job_node_type = 'process.calculation.calcjob.CalcJobNode.'
    node_data = data['export_data'].get('Node', {})
    node_attributes = data['node_attributes']
    calc_jobs = {}
    for pk, values in node_data.items():
        if values['node_type'] == calc_job_node_type and 'state' in data['node_attributes'].get(pk, {}):
            calc_jobs[pk] = data['node_attributes'][pk]['state']

    # Migrate to v0.6
    metadata, data = migrate_from_func('export_0.5_simple.aiida', '0.5', '0.6', migrate_v5_to_v6, core_archive)
    verify_metadata_version(metadata, version='0.6')

    node_attributes = data['node_attributes']

    # The export archive contains a single `CalcJobNode` that had `state=FINISHED`.
    for pk, state in calc_jobs.items():
        attributes = node_attributes[pk]

        if STATE_MAPPING[state].exit_status is not None:
            assert attributes['exit_status'] == STATE_MAPPING[state].exit_status

        if STATE_MAPPING[state].process_state is not None:
            assert attributes['process_state'] == STATE_MAPPING[state].process_state

        if STATE_MAPPING[state].process_status is not None:
            assert attributes['process_status'] == STATE_MAPPING[state].process_status

        assert attributes['process_label'] == 'Legacy JobCalculation'


def test_migrate_v5_to_v6_datetime(core_archive, migrate_from_func):
    """Test the data migration of serialized datetime objects.

    Datetime attributes were serialized into strings, by first converting to UTC and then printing with the format
    '%Y-%m-%dT%H:%M:%S.%f'. In the database migration, datetimes were serialized *including* timezone information.
    Here we test that the archive migration correctly reattaches the timezone information. The archive that we are
    using `export_0.5_simple.aiida` contains a node with the attribute "scheduler_lastchecktime".
    """
    # Get metadata.json and data.json as dicts from v0.5 file archive
    archive_path = get_archive_file('export_0.5_simple.aiida', **core_archive)
    metadata, data = read_json_files(archive_path)

    verify_metadata_version(metadata, version='0.5')

    for key, values in data['node_attributes'].items():
        if 'scheduler_lastchecktime' not in values:
            continue

        serialized_original = values['scheduler_lastchecktime']
        msg = f'the serialized datetime before migration should not contain a plus: {serialized_original}'
        assert '+' not in serialized_original, msg

        # Migrate to v0.6
        metadata, data = migrate_from_func('export_0.5_simple.aiida', '0.5', '0.6', migrate_v5_to_v6, core_archive)
        verify_metadata_version(metadata, version='0.6')

        serialized_migrated = data['node_attributes'][key]['scheduler_lastchecktime']
        assert serialized_migrated == f'{serialized_original}+00:00'
        break

    else:
        raise RuntimeError(
            'the archive `export_0.5_simple.aiida` did not contain a node with the attribute '
            '`scheduler_lastchecktime` which is required for this test.'
        )
