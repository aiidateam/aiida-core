# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Shared function for django_0024 and sqlalchemy ea2f50e7f615"""
import sys
from tempfile import NamedTemporaryFile
from typing import Set

import click
import sqlalchemy as sa

from aiida.cmdline.utils import echo

from .utils import dumps_json


def get_legacy_workflow_log_number(connection):
    """ Get the number of the log records that correspond to legacy workflows """
    return connection.execute(
        sa.text(
            """
        SELECT COUNT(*) FROM db_dblog
        WHERE
            (db_dblog.objname LIKE 'aiida.workflows.user.%')
        """
        )
    ).fetchall()[0][0]


def get_unknown_entity_log_number(connection):
    """ Get the number of the log records that correspond to unknown entities """
    return connection.execute(
        sa.text(
            """
        SELECT COUNT(*) FROM db_dblog
        WHERE
            (db_dblog.objname NOT LIKE 'node.%') AND
            (db_dblog.objname NOT LIKE 'aiida.workflows.user.%')
        """
        )
    ).fetchall()[0][0]


def get_logs_with_no_nodes_number(connection):
    """ Get the number of the log records that correspond to nodes that were deleted """
    return connection.execute(
        sa.text(
            """
        SELECT COUNT(*) FROM db_dblog
        WHERE
            (db_dblog.objname LIKE 'node.%') AND NOT EXISTS
            (SELECT 1 FROM db_dbnode WHERE db_dbnode.id = db_dblog.objpk LIMIT 1)
        """
        )
    ).fetchall()[0][0]


def get_serialized_legacy_workflow_logs(connection):
    """ Get the serialized log records that correspond to legacy workflows """
    query = connection.execute(
        sa.text(
            """
        SELECT db_dblog.id, db_dblog.time, db_dblog.loggername, db_dblog.levelname, db_dblog.objpk, db_dblog.objname,
        db_dblog.message, db_dblog.metadata FROM db_dblog
        WHERE
            (db_dblog.objname LIKE 'aiida.workflows.user.%')
        """
        )
    )
    res = []
    for row in query:
        res.append(row._asdict())
    return dumps_json(res)


def get_serialized_unknown_entity_logs(connection):
    """ Get the serialized log records that correspond to unknown entities """
    query = connection.execute(
        sa.text(
            """
        SELECT db_dblog.id, db_dblog.time, db_dblog.loggername, db_dblog.levelname, db_dblog.objpk, db_dblog.objname,
        db_dblog.message, db_dblog.metadata FROM db_dblog
        WHERE
            (db_dblog.objname NOT LIKE 'node.%') AND
            (db_dblog.objname NOT LIKE 'aiida.workflows.user.%')
        """
        )
    )
    res = []
    for row in query:
        res.append(row._asdict())
    return dumps_json(res)


def get_serialized_logs_with_no_nodes(connection):
    """ Get the serialized log records that correspond to nodes that were deleted """
    query = connection.execute(
        sa.text(
            """
        SELECT db_dblog.id, db_dblog.time, db_dblog.loggername, db_dblog.levelname, db_dblog.objpk, db_dblog.objname,
        db_dblog.message, db_dblog.metadata FROM db_dblog
        WHERE
            (db_dblog.objname LIKE 'node.%') AND NOT EXISTS
            (SELECT 1 FROM db_dbnode WHERE db_dbnode.id = db_dblog.objpk LIMIT 1)
        """
        )
    )
    res = []
    for row in query:
        res.append(row._asdict())
    return dumps_json(res)


def export_and_clean_workflow_logs(connection, profile):
    """Export the logs records that correspond to legacy workflows and to unknown entities
    (place them to files and remove them from the DbLog table).
    """
    lwf_no_number = get_legacy_workflow_log_number(connection)
    other_number = get_unknown_entity_log_number(connection)
    log_no_node_number = get_logs_with_no_nodes_number(connection)

    # If there are no legacy workflow log records or log records of an unknown entity
    if lwf_no_number == 0 and other_number == 0 and log_no_node_number == 0:
        return

    if not profile.is_test_profile:
        echo.echo_warning(
            'We found {} log records that correspond to legacy workflows and {} log records to correspond '
            'to an unknown entity.'.format(lwf_no_number, other_number)
        )
        echo.echo_warning(
            'These records will be removed from the database and exported to JSON files (to the current directory).'
        )
        proceed = click.confirm('Would you like to proceed?', default=True)
        if not proceed:
            sys.exit(1)

    delete_on_close = profile.is_test_profile

    # Exporting the legacy workflow log records
    if lwf_no_number != 0:

        # Get the records and write them to file
        with NamedTemporaryFile(
            prefix='legagy_wf_logs-', suffix='.log', dir='.', delete=delete_on_close, mode='w+'
        ) as handle:
            # Export the log records
            filename = handle.name
            handle.write(get_serialized_legacy_workflow_logs(connection))

            # If delete_on_close is False, we are running for the user and add additional message of file location
            if not delete_on_close:
                echo.echo(f'Exported legacy workflow logs to {filename}')

        # Now delete the records
        connection.execute(
            sa.text(
                """
            DELETE FROM db_dblog
            WHERE
                (db_dblog.objname LIKE 'aiida.workflows.user.%')
            """
            )
        )

    # Exporting unknown log records
    if other_number != 0:
        # Get the records and write them to file
        with NamedTemporaryFile(
            prefix='unknown_entity_logs-', suffix='.log', dir='.', delete=delete_on_close, mode='w+'
        ) as handle:
            # Export the log records
            filename = handle.name
            handle.write(get_serialized_unknown_entity_logs(connection))

            # If delete_on_close is False, we are running for the user and add additional message of file location
            if not delete_on_close:
                echo.echo(f'Exported unexpected entity logs to {filename}')

        # Now delete the records
        connection.execute(
            sa.text(
                """
            DELETE FROM db_dblog WHERE
                (db_dblog.objname NOT LIKE 'node.%') AND
                (db_dblog.objname NOT LIKE 'aiida.workflows.user.%')
            """
            )
        )

    # Exporting log records that don't correspond to nodes
    if log_no_node_number != 0:
        # Get the records and write them to file
        with NamedTemporaryFile(
            prefix='no_node_entity_logs-', suffix='.log', dir='.', delete=delete_on_close, mode='w+'
        ) as handle:
            # Export the log records
            filename = handle.name
            handle.write(get_serialized_logs_with_no_nodes(connection))

            # If delete_on_close is False, we are running for the user and add additional message of file location
            if not delete_on_close:
                echo.echo(f'Exported entity logs that do not correspond to nodes to {filename}')

        # Now delete the records
        connection.execute(
            sa.text(
                """
            DELETE FROM db_dblog WHERE
            (db_dblog.objname LIKE 'node.%') AND NOT EXISTS
            (SELECT 1 FROM db_dbnode WHERE db_dbnode.id = db_dblog.objpk LIMIT 1)
            """
            )
        )


def set_new_uuid(connection):
    """ Set new and distinct UUIDs to all the logs """
    from aiida.common.utils import get_new_uuid

    # Exit if there are no rows - e.g. initial setup
    id_query = connection.execute(sa.text('SELECT db_dblog.id FROM db_dblog'))
    if id_query.rowcount == 0:
        return

    id_res = id_query.fetchall()
    ids = []
    for (curr_id,) in id_res:
        ids.append(curr_id)
    uuids: Set[str] = set()
    while len(uuids) < len(ids):
        uuids.add(get_new_uuid())

    # Create the key/value pairs
    key_values = ','.join(f"({curr_id}, '{curr_uuid}')" for curr_id, curr_uuid in zip(ids, uuids))

    update_stm = f"""
        UPDATE db_dblog as t SET
            uuid = uuid(c.uuid)
        from (values {key_values}) as c(id, uuid) where c.id = t.id"""
    connection.execute(sa.text(update_stm))
