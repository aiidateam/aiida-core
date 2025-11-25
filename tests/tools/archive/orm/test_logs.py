###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm.Log tests for the export and import routines"""

from aiida import orm
from aiida.tools.archive import create_archive, import_archive


def test_critical_log_msg_and_metadata(tmp_path, aiida_profile_clean):
    """Testing logging of critical message"""
    message = 'Testing logging of critical failure'
    calc = orm.CalculationNode()

    # Firing a log for an unstored node should not end up in the database
    calc.logger.critical(message)
    # There should be no log messages for the unstored object
    assert len(orm.Log.collection.all()) == 0

    # After storing the node, logs above log level should be stored
    calc.store()
    calc.seal()
    calc.logger.critical(message)

    # Store Log metadata
    log_metadata = orm.Log.collection.get(dbnode_id=calc.pk).metadata

    export_file = tmp_path.joinpath('export.aiida')
    create_archive([calc], filename=export_file)

    aiida_profile_clean.reset_storage()

    import_archive(export_file)

    # Finding all the log messages
    logs = orm.Log.collection.all()

    assert len(logs) == 1
    assert logs[0].message == message
    assert logs[0].metadata == log_metadata


def test_exclude_logs_flag(tmp_path, aiida_profile_clean):
    """Test that the `include_logs` argument for `export` works."""
    log_msg = 'Testing logging of critical failure'

    # Create node
    calc = orm.CalculationNode()
    calc.store()
    calc.seal()

    # Create log message
    calc.logger.critical(log_msg)

    # Save uuids prior to export
    calc_uuid = calc.uuid

    # Export, excluding logs
    export_file = tmp_path.joinpath('export.aiida')
    create_archive([calc], filename=export_file, include_logs=False)

    # Clean database and reimport exported data
    aiida_profile_clean.reset_storage()
    import_archive(export_file)

    # Finding all the log messages
    import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid']).all()
    import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()

    # There should be exactly: 1 orm.CalculationNode, 0 Logs
    assert len(import_calcs) == 1
    assert len(import_logs) == 0

    # Check it's the correct node
    assert str(import_calcs[0][0]) == calc_uuid


def test_export_of_imported_logs(tmp_path, aiida_profile_clean):
    """Test export of imported Log"""
    log_msg = 'Testing export of imported log'

    # Create node
    calc = orm.CalculationNode()
    calc.store()
    calc.seal()

    # Create log message
    calc.logger.critical(log_msg)

    # Save uuids prior to export
    calc_uuid = calc.uuid
    log_uuid = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()
    log_uuid = str(log_uuid[0][0])

    # Export
    export_file = tmp_path.joinpath('export.aiida')
    create_archive([calc], filename=export_file)

    # Clean database and reimport exported data
    aiida_profile_clean.reset_storage()
    import_archive(export_file)

    # Finding all the log messages
    import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid']).all()
    import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()

    # There should be exactly: 1 CalculationNode, 1 Log
    assert len(import_calcs) == 1
    assert len(import_logs) == 1

    # Check the UUIDs are the same
    assert str(import_calcs[0][0]) == calc_uuid
    assert str(import_logs[0][0]) == log_uuid

    # Re-export
    calc = orm.load_node(import_calcs[0][0])
    re_export_file = tmp_path.joinpath('re_export.aiida')
    create_archive([calc], filename=re_export_file)

    # Clean database and reimport exported data
    aiida_profile_clean.reset_storage()
    import_archive(re_export_file)

    # Finding all the log messages
    import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid']).all()
    import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()

    # There should be exactly: 1 CalculationNode, 1 Log
    assert len(import_calcs) == 1
    assert len(import_logs) == 1

    # Check the UUIDs are the same
    assert str(import_calcs[0][0]) == calc_uuid
    assert str(import_logs[0][0]) == log_uuid


def test_multiple_imports_for_single_node(tmp_path, aiida_profile_clean):
    """Test multiple imports for single node with different logs are imported correctly"""
    log_msgs = ['Life is like riding a bicycle.', 'To keep your balance,', 'you must keep moving.']

    # Create Node and initial log message and save UUIDs prior to export
    node = orm.CalculationNode().store()
    node.seal()
    node.logger.critical(log_msgs[0])
    node_uuid = node.uuid
    log_uuid_existing = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()
    log_uuid_existing = str(log_uuid_existing[0][0])

    # Export as "EXISTING" DB
    export_file_existing = tmp_path.joinpath('export_EXISTING.aiida')
    create_archive([node], filename=export_file_existing)

    # Add 2 more Logs and save UUIDs for all three Logs prior to export
    node.logger.critical(log_msgs[1])
    node.logger.critical(log_msgs[2])
    log_uuids_full = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()
    log_uuids_full = [str(log[0]) for log in log_uuids_full]

    # Export as "FULL" DB
    export_file_full = tmp_path.joinpath('export_FULL.aiida')
    create_archive([node], filename=export_file_full)

    # Clean database and reimport "EXISTING" DB
    aiida_profile_clean.reset_storage()
    import_archive(export_file_existing)

    # Check correct import
    builder = orm.QueryBuilder().append(orm.Node, tag='node', project=['uuid'])
    builder.append(orm.Log, with_node='node', project=['uuid', 'message'])
    builder = builder.all()

    assert len(builder) == 1  # There is 1 Log in "EXISTING" DB

    imported_node_uuid = builder[0][0]
    assert imported_node_uuid == node_uuid

    imported_log_uuid = builder[0][1]
    imported_log_message = builder[0][2]
    assert imported_log_uuid == log_uuid_existing
    assert imported_log_message == log_msgs[0]

    # Import "FULL" DB
    import_archive(export_file_full)

    # Since the UUID of the node is identical with the node already in the DB,
    # the Logs should be added to the existing node, avoiding the addition of
    # the single Log already present.
    # Check this by retrieving all Logs for the node.
    builder = orm.QueryBuilder().append(orm.Node, tag='node', project=['uuid'])
    builder.append(orm.Log, with_node='node', project=['uuid', 'message'])
    builder = builder.all()

    assert len(builder) == len(log_msgs)  # There should now be 3 Logs

    imported_node_uuid = builder[0][0]
    assert imported_node_uuid == node_uuid
    for log in builder:
        imported_log_uuid = log[1]
        imported_log_content = log[2]

        assert imported_log_uuid in log_uuids_full
        assert imported_log_content in log_msgs


def test_reimport_of_logs_for_single_node(tmp_path, aiida_profile_clean):
    """When a node with logs already exist in the DB, and more logs are imported
    for the same node (same UUID), test that only new log-entries are added.

    Part I:
    Create CalculationNode and 1 Log for it.
    Export CalculationNode with its 1 Log to archive file #1 "EXISTING database".
    Add 2 Logs to CalculationNode.
    Export CalculationNode with its 3 Logs to archive file #2 "FULL database".
    Reset database.

    Part II:
    Reimport archive file #1 "EXISTING database".
    Add 2 Logs to CalculationNode (different UUID than for "FULL database").
    Export CalculationNode with its 3 Logs to archive file #3 "NEW database".
    Reset database.

    Part III:
    Reimport archive file #1 "EXISTING database" (1 CalculationNode, 1 Log).
    Import archive file #2 "FULL database" (1 CalculationNode, 3 Logs).
    Check the database EXACTLY contains 1 CalculationNode and 3 Logs,
    with matching UUIDS all the way through all previous Parts.

    Part IV:
    Import archive file #3 "NEW database" (1 CalculationNode, 3 Logs).
    Check the database EXACTLY contains 1 CalculationNode and 5 Logs,
    with matching UUIDS all the way through all previous Parts.
    NB! There should now be 5 Logs in the database. 4 of which are identical
    in pairs, except for their UUID.
    """
    export_filenames = {
        'EXISTING': 'export_EXISTING_db.tar.gz',
        'FULL': 'export_FULL_db.tar.gz',
        'NEW': 'export_NEW_db.tar.gz',
    }

    log_msgs = ['Life is like riding a bicycle.', 'To keep your balance,', 'you must keep moving.']

    ## Part I
    # Create node and save UUID
    calc = orm.CalculationNode()
    calc.store()
    calc.seal()
    calc_uuid = calc.uuid

    # Create first log message
    calc.logger.critical(log_msgs[0])

    # There should be exactly: 1 CalculationNode, 1 Log
    export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
    export_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
    assert export_calcs.count() == 1
    assert export_logs.count() == 1

    # Save Log UUID before export
    existing_log_uuids = [str(export_logs.all()[0][0])]

    # Export "EXISTING" DB
    export_file_existing = tmp_path.joinpath(export_filenames['EXISTING'])
    create_archive([calc], filename=export_file_existing)

    # Add remaining Log messages
    for log_msg in log_msgs[1:]:
        calc.logger.critical(log_msg)

    # There should be exactly: 1 CalculationNode, 3 Logs (len(log_msgs))
    export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
    export_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
    assert export_calcs.count() == 1
    assert export_logs.count() == len(log_msgs)

    # Save Log UUIDs before export, there should be 3 UUIDs in total (len(log_msgs))
    full_log_uuids = set(existing_log_uuids)
    for log_uuid in export_logs.all():
        full_log_uuids.add(str(log_uuid[0]))
    assert len(full_log_uuids) == len(log_msgs)

    # Export "FULL" DB
    export_file_full = tmp_path.joinpath(export_filenames['FULL'])
    create_archive([calc], filename=export_file_full)

    # Clean database
    aiida_profile_clean.reset_storage()

    ## Part II
    # Reimport "EXISTING" DB
    import_archive(export_file_existing)

    # Check the database is correctly imported.
    # There should be exactly: 1 CalculationNode, 1 Log
    import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
    import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
    assert import_calcs.count() == 1
    assert import_logs.count() == 1
    # Furthermore, the UUIDs should be the same
    assert str(import_calcs.all()[0][0]) == calc_uuid
    assert str(import_logs.all()[0][0]) in existing_log_uuids

    # Add remaining Log messages (again)
    calc = orm.load_node(import_calcs.all()[0][0])
    for log_msg in log_msgs[1:]:
        calc.logger.critical(log_msg)

    # There should be exactly: 1 CalculationNode, 3 Logs (len(log_msgs))
    export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
    export_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
    assert export_calcs.count() == 1
    assert export_logs.count() == len(log_msgs)

    # Save Log UUIDs before export, there should be 3 UUIDs in total (len(log_msgs))
    new_log_uuids = set(existing_log_uuids)
    for log_uuid in export_logs.all():
        new_log_uuids.add(str(log_uuid[0]))
    assert len(new_log_uuids) == len(log_msgs)

    # Export "NEW" DB
    export_file_new = tmp_path.joinpath(export_filenames['NEW'])
    create_archive([calc], filename=export_file_new)

    # Clean database
    aiida_profile_clean.reset_storage()

    ## Part III
    # Reimport "EXISTING" DB
    import_archive(export_file_existing)

    # Check the database is correctly imported.
    # There should be exactly: 1 CalculationNode, 1 Log
    import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
    import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
    assert import_calcs.count() == 1
    assert import_logs.count() == 1
    # Furthermore, the UUIDs should be the same
    assert str(import_calcs.all()[0][0]) == calc_uuid
    assert str(import_logs.all()[0][0]) in existing_log_uuids

    # Import "FULL" DB
    import_archive(export_file_full)

    # Check the database is correctly imported.
    # There should be exactly: 1 CalculationNode, 3 Logs (len(log_msgs))
    import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
    import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
    assert import_calcs.count() == 1
    assert import_logs.count() == len(log_msgs)
    # Furthermore, the UUIDs should be the same
    assert str(import_calcs.all()[0][0]) == calc_uuid
    for log in import_logs.all():
        log_uuid = str(log[0])
        assert log_uuid in full_log_uuids

    ## Part IV
    # Import "NEW" DB
    import_archive(export_file_new)

    # Check the database is correctly imported.
    # There should be exactly: 1 CalculationNode, 5 Logs (len(log_msgs))
    # 4 of the logs are identical in pairs, except for the UUID.
    import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
    import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid', 'message'])
    assert import_calcs.count() == 1
    assert import_logs.count() == 5
    # Furthermore, the UUIDs should be the same
    assert str(import_calcs.all()[0][0]) == calc_uuid
    total_log_uuids = full_log_uuids.copy()
    total_log_uuids.update(new_log_uuids)
    for log in import_logs.all():
        log_uuid = str(log[0])
        log_message = str(log[1])
        assert log_uuid in total_log_uuids
        assert log_message in log_msgs


def test_filter_size(tmp_path, aiida_profile_clean):
    """Tests if the query still works when the number of logs is beyond the `filter_size limit."""
    node = orm.CalculationNode().store()
    node.seal()

    nb_nodes = 5
    for _ in range(nb_nodes):
        node.logger.critical('some')

    # Export DB
    export_file_existing = tmp_path.joinpath('export.aiida')
    create_archive([node], filename=export_file_existing)

    # Clean database and reimport DB
    aiida_profile_clean.reset_storage()
    import_archive(export_file_existing, filter_size=2)

    # Check correct import
    builder = orm.QueryBuilder().append(orm.Node, tag='node', project=['uuid'])
    builder.append(orm.Log, with_node='node', project=['uuid'])
    builder = builder.all()

    assert len(builder) == nb_nodes
