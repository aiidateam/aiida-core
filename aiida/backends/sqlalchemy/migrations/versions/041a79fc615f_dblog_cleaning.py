# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member,import-error,no-name-in-module
"""This migration cleans the log records from non-Node entity records.
It removes from the DbLog table the legacy workflow records and records
that correspond to an unknown entity and places them to corresponding files.

This migration corresponds to the 0024_dblog_update Django migration.

Revision ID: 041a79fc615f
Revises: 7ca08c391c49
Create Date: 2018-12-28 15:53:14.596810
"""
# pylint: disable=wrong-import-order
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import sys
from six.moves import zip
import click
import sqlalchemy as sa
from sqlalchemy.sql import text
from alembic import op

from aiida import settings
from aiida.backends.sqlalchemy.utils import dumps_json

# revision identifiers, used by Alembic.
revision = '041a79fc615f'
down_revision = '7ca08c391c49'
branch_labels = None
depends_on = None

# The values that will be exported for the log records that will be deleted
values_to_export = ['id', 'time', 'loggername', 'levelname', 'objpk', 'objname', 'message', 'metadata']


def get_legacy_workflow_log_number(connection):
    """ Get the number of the log records that correspond to legacy workflows """
    return connection.execute(
        text("""
        SELECT COUNT(*) FROM db_dblog
        WHERE
            (db_dblog.objname LIKE 'aiida.workflows.user.%')
        """)).fetchall()[0][0]


def get_unknown_entity_log_number(connection):
    """ Get the number of the log records that correspond to unknown entities """
    return connection.execute(
        text("""
        SELECT COUNT(*) FROM db_dblog
        WHERE
            (db_dblog.objname NOT LIKE 'node.%') AND
            (db_dblog.objname NOT LIKE 'aiida.workflows.user.%')
        """)).fetchall()[0][0]


def get_logs_with_no_nodes_number(connection):
    """ Get the number of the log records that correspond to nodes that were deleted """
    return connection.execute(
        text("""
        SELECT COUNT(*) FROM db_dblog
        WHERE
            (db_dblog.objname LIKE 'node.%') AND NOT EXISTS
            (SELECT 1 FROM db_dbnode WHERE db_dbnode.id = db_dblog.objpk LIMIT 1)
        """)).fetchall()[0][0]


def get_serialized_legacy_workflow_logs(connection):
    """ Get the serialized log records that correspond to legacy workflows """
    query = connection.execute(
        text("""
        SELECT db_dblog.id, db_dblog.time, db_dblog.loggername, db_dblog.levelname, db_dblog.objpk, db_dblog.objname,
        db_dblog.message, db_dblog.metadata FROM db_dblog
        WHERE
            (db_dblog.objname LIKE 'aiida.workflows.user.%')
        """))
    res = list()
    for row in query:
        res.append(dict(list(zip(row.keys(), row))))
    return dumps_json(res)


def get_serialized_unknown_entity_logs(connection):
    """ Get the serialized log records that correspond to unknown entities """
    query = connection.execute(
        text("""
        SELECT db_dblog.id, db_dblog.time, db_dblog.loggername, db_dblog.levelname, db_dblog.objpk, db_dblog.objname,
        db_dblog.message, db_dblog.metadata FROM db_dblog
        WHERE
            (db_dblog.objname NOT LIKE 'node.%') AND
            (db_dblog.objname NOT LIKE 'aiida.workflows.user.%')
        """))
    res = list()
    for row in query:
        res.append(dict(list(zip(row.keys(), row))))
    return dumps_json(res)


def get_serialized_logs_with_no_nodes(connection):
    """ Get the serialized log records that correspond to nodes that were deleted """
    query = connection.execute(
        text("""
        SELECT db_dblog.id, db_dblog.time, db_dblog.loggername, db_dblog.levelname, db_dblog.objpk, db_dblog.objname,
        db_dblog.message, db_dblog.metadata FROM db_dblog
        WHERE
            (db_dblog.objname LIKE 'node.%') AND NOT EXISTS
            (SELECT 1 FROM db_dbnode WHERE db_dbnode.id = db_dblog.objpk LIMIT 1)
        """))
    res = list()
    for row in query:
        res.append(dict(list(zip(row.keys(), row))))
    return dumps_json(res)


def export_and_clean_workflow_logs(connection):
    """
    Export the logs records that correspond to legacy workflows and to unknown entities (place them to files
    and remove them from the DbLog table).
    """
    from tempfile import NamedTemporaryFile

    lwf_no_number = get_legacy_workflow_log_number(connection)
    other_number = get_unknown_entity_log_number(connection)
    log_no_node_number = get_logs_with_no_nodes_number(connection)

    # If there are no legacy workflow log records or log records of an unknown entity
    if lwf_no_number == 0 and other_number == 0 and log_no_node_number == 0:
        return

    if not settings.TESTING_MODE:
        click.echo('We found {} log records that correspond to legacy workflows and {} log records to correspond '
                   'to an unknown entity.'.format(lwf_no_number, other_number))
        click.echo(
            'These records will be removed from the database and exported to JSON files to the current directory).')
        proceed = click.confirm('Would you like to proceed?', default=True)
        if not proceed:
            sys.exit(1)

    delete_on_close = False
    if settings.TESTING_MODE:
        delete_on_close = True

    # Exporting the legacy workflow log records
    if lwf_no_number != 0:

        # Get the records and write them to file
        with NamedTemporaryFile(
                prefix='legagy_wf_logs-', suffix='.log', dir='.', delete=delete_on_close, mode='w+') as handle:
            # Export the log records
            filename = handle.name
            handle.write(get_serialized_legacy_workflow_logs(connection))

            # If delete_on_close is False, we are running for the user and add additional message of file location
            if not delete_on_close:
                click.echo('Exported legacy workflow logs to {}'.format(filename))

        # Now delete the records
        connection.execute(
            text("""
            DELETE FROM db_dblog
            WHERE
                (db_dblog.objname LIKE 'aiida.workflows.user.%')
            """))

    # Exporting unknown log records
    if other_number != 0:
        # Get the records and write them to file
        with NamedTemporaryFile(
                prefix='unknown_entity_logs-', suffix='.log', dir='.', delete=delete_on_close, mode='w+') as handle:
            # Export the log records
            filename = handle.name
            handle.write(get_serialized_unknown_entity_logs(connection))

            # If delete_on_close is False, we are running for the user and add additional message of file location
            if not delete_on_close:
                click.echo('Exported unexpected entity logs to {}'.format(filename))

        # Now delete the records
        connection.execute(
            text("""
            DELETE FROM db_dblog WHERE
                (db_dblog.objname NOT LIKE 'node.%') AND
                (db_dblog.objname NOT LIKE 'aiida.workflows.user.%')
            """))

    # Exporting log records that don't correspond to nodes
    if log_no_node_number != 0:
        # Get the records and write them to file
        with NamedTemporaryFile(
                prefix='no_node_entity_logs-', suffix='.log', dir='.', delete=delete_on_close, mode='w+') as handle:
            # Export the log records
            filename = handle.name
            handle.write(get_serialized_logs_with_no_nodes(connection))

            # If delete_on_close is False, we are running for the user and add additional message of file location
            if not delete_on_close:
                click.echo('Exported entity logs that don\'t correspond to nodes to {}'.format(filename))

        # Now delete the records
        connection.execute(
            text("""
            DELETE FROM db_dblog WHERE
            (db_dblog.objname LIKE 'node.%') AND NOT EXISTS
            (SELECT 1 FROM db_dbnode WHERE db_dbnode.id = db_dblog.objpk LIMIT 1)
            """))


def upgrade():
    """
    Changing the log table columns to use uuid to reference remote objects and log entries.
    Upgrade function.
    """
    connection = op.get_bind()

    # Clean data
    export_and_clean_workflow_logs(connection)

    # Create the dbnode_id column and add the necessary index
    op.add_column('db_dblog', sa.Column('dbnode_id', sa.INTEGER(), autoincrement=False, nullable=True))
    # Transfer data to dbnode_id from objpk
    connection.execute(text("""UPDATE db_dblog SET dbnode_id=objpk"""))

    op.create_foreign_key(
        None,
        "db_dblog",
        "db_dbnode", ['dbnode_id'], ['id'],
        ondelete=u'CASCADE',
        initially=u'DEFERRED',
        deferrable=True)

    # Update the dbnode_id column to not nullable
    op.alter_column('db_dblog', 'dbnode_id', nullable=False)

    # Remove the objpk column
    op.drop_column('db_dblog', 'objpk')

    # Remove the objname column
    op.drop_column('db_dblog', 'objname')

    # Remove objpk and objname from metadata dictionary
    connection.execute(text("""UPDATE db_dblog SET metadata = metadata - 'objpk' - 'objname' """))


def downgrade():
    """
    Downgrade function to the previous schema.
    """
    # Create an empty column objname (the data is permanently lost)
    op.add_column('db_dblog', sa.Column('objname', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.create_index('ix_db_dblog_objname', 'db_dblog', ['objname'])

    # Creating a column objpk -
    op.add_column('db_dblog', sa.Column('objpk', sa.INTEGER(), autoincrement=False, nullable=True))

    # Copy the data back to objpk from dbnode_id
    op.execute(text("""UPDATE db_dblog SET objpk=dbnode_id"""))

    # Removing the column dbnode_id
    op.drop_column('db_dblog', 'dbnode_id')

    # Populate objname with correct values
    op.execute(
        text("""UPDATE db_dblog SET objname=db_dbnode.type
    FROM db_dbnode WHERE db_dbnode.id = db_dblog.objpk"""))

    # Enrich metadata with objpk and objname if these keys don't exist
    op.execute(
        text("""UPDATE db_dblog SET metadata = jsonb_set(metadata, '{"objpk"}', to_jsonb(objpk))
    WHERE NOT (metadata ?| '{"objpk"}') """))
    op.execute(
        text("""UPDATE db_dblog SET metadata = jsonb_set(metadata, '{"objname"}', to_jsonb(objname))
    WHERE NOT (metadata ?| '{"objname"}') """))
