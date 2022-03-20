# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member
"""Clean the log records from non-Node entity records (part a).

It removes from the ``DbLog`` table, the legacy workflow records and records
that correspond to an unknown entity and places them to corresponding files.

Note this migration is similar to the sqlalchemy migration 041a79fc615f + ea2f50e7f615

Revision ID: django_0024a
Revises: django_0023

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from aiida.storage.psql_dos.migrations.utils.dblog_update import export_and_clean_workflow_logs, set_new_uuid

revision = 'django_0024a'
down_revision = 'django_0023'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    connection = op.get_bind()

    # Clean data
    export_and_clean_workflow_logs(connection, op.get_context().opts['aiida_profile'])

    # Note, we could also remove objpk and objname from the metadata dictionary here,
    # but since this is not yet a JSONB column, it would be a costly operation, so we skip it for now.

    # Create a new column, which is a foreign key to the dbnode table
    op.add_column(
        'db_dblog', sa.Column('dbnode_id', sa.INTEGER(), autoincrement=False, nullable=False, server_default='1')
    )

    # Transfer data to dbnode_id from objpk
    connection.execute(sa.text("""UPDATE db_dblog SET dbnode_id=objpk"""))

    # Create the foreign key constraint and index
    op.create_foreign_key(
        'db_dblog_dbnode_id_da34b732_fk_db_dbnode_id',
        'db_dblog',
        'db_dbnode', ['dbnode_id'], ['id'],
        initially='DEFERRED',
        deferrable=True
        # note, the django migration added on_delete='CASCADE', however, this does not actually set it on the database,
        # see: https://stackoverflow.com/a/35780859/5033292
    )
    op.create_index('db_dblog_dbnode_id_da34b732', 'db_dblog', ['dbnode_id'], unique=False)

    # Now that all the data have been migrated, remove the server default, and unnecessary columns
    op.alter_column('db_dblog', 'dbnode_id', server_default=None)
    op.drop_column('db_dblog', 'objpk')
    op.drop_column('db_dblog', 'objname')

    # Create the UUID column, with a default UUID value
    op.add_column(
        'db_dblog',
        sa.Column(
            'uuid',
            postgresql.UUID(),
            nullable=False,
            server_default='f6a16ff7-4a31-11eb-be7b-8344edc8f36b',
        )
    )
    op.alter_column('db_dblog', 'uuid', server_default=None)

    # Set unique uuids on the column rows
    set_new_uuid(connection)

    # we now want to set the unique constraint
    # however, this gives: cannot ALTER TABLE "db_dblog" because it has pending trigger events
    # so we do this in a follow up migration (which takes place in a new transaction)
    # op.create_unique_constraint('db_dblog_uuid_9cf77df3_uniq', 'db_dblog', ['uuid'])


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0024a.')
