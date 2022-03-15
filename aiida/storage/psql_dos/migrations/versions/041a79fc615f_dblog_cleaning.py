# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member,import-error,no-name-in-module,protected-access
"""This migration cleans the log records from non-Node entity records.

It removes from the DbLog table the legacy workflow records and records
that correspond to an unknown entity and places them to corresponding files.

This migration corresponds to the 0024_dblog_update Django migration (except without uuid addition).

Revision ID: 041a79fc615f
Revises: 7ca08c391c49
Create Date: 2018-12-28 15:53:14.596810
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

from aiida.storage.psql_dos.migrations.utils.dblog_update import export_and_clean_workflow_logs

# revision identifiers, used by Alembic.
revision = '041a79fc615f'
down_revision = '7ca08c391c49'
branch_labels = None
depends_on = None


def upgrade():
    """
    Changing the log table columns to use uuid to reference remote objects and log entries.
    Upgrade function.
    """
    connection = op.get_bind()

    # Clean data
    export_and_clean_workflow_logs(connection, op.get_context().opts['aiida_profile'])

    # Remove objpk and objname from the metadata dictionary
    connection.execute(text("""UPDATE db_dblog SET metadata = metadata - 'objpk' - 'objname' """))

    # Create a new column, which is a foreign key to the dbnode table
    op.add_column('db_dblog', sa.Column('dbnode_id', sa.INTEGER(), autoincrement=False, nullable=True))
    # Transfer data to dbnode_id from objpk
    connection.execute(text("""UPDATE db_dblog SET dbnode_id=objpk"""))
    op.create_foreign_key(
        'db_dblog_dbnode_id_fkey',
        'db_dblog',
        'db_dbnode', ['dbnode_id'], ['id'],
        ondelete='CASCADE',
        initially='DEFERRED',
        deferrable=True
    )

    # Now that all the data have been migrated, make the column not nullable and not blank.
    # A log record should always correspond to a node record
    op.alter_column('db_dblog', 'dbnode_id', nullable=False)

    # Remove the objpk column
    op.drop_column('db_dblog', 'objpk')

    # Remove the objname column
    op.drop_column('db_dblog', 'objname')


def downgrade():
    """
    Downgrade function to the previous schema.
    """
    raise NotImplementedError('Downgrade of 041a79fc615f.')
