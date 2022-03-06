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
"""Replace null values with defaults

Revision ID: main_0000a
Revises: main_0000
Create Date: 2022-03-04

"""
from alembic import op
import sqlalchemy as sa

from aiida.common import timezone

# revision identifiers, used by Alembic.
revision = 'main_0000a'
down_revision = 'main_0000'
branch_labels = None
depends_on = None


def upgrade():  # pylint: disable=too-many-statements
    """Convert null values to default values.

    This migration is performed in preparation for the next migration,
    which will make these fields non-nullable.
    """
    db_dbauthinfo = sa.sql.table(
        'db_dbauthinfo',
        sa.sql.column('aiidauser_id', sa.Integer),
        sa.sql.column('dbcomputer_id', sa.Integer),
        sa.Column('enabled', sa.Boolean),
        sa.Column('auth_params', sa.JSON),
        sa.Column('metadata', sa.JSON()),
    )

    # remove rows with null values, which may have previously resulted from deletion of a user or computer
    op.execute(db_dbauthinfo.delete().where(db_dbauthinfo.c.aiidauser_id.is_(None)))  # type: ignore[arg-type]
    op.execute(db_dbauthinfo.delete().where(db_dbauthinfo.c.dbcomputer_id.is_(None)))  # type: ignore[arg-type]

    op.execute(db_dbauthinfo.update().where(db_dbauthinfo.c.enabled.is_(None)).values(enabled=True))
    op.execute(db_dbauthinfo.update().where(db_dbauthinfo.c.auth_params.is_(None)).values(auth_params={}))
    op.execute(db_dbauthinfo.update().where(db_dbauthinfo.c.metadata.is_(None)).values(metadata={}))

    db_dbcomment = sa.sql.table(
        'db_dbcomment',
        sa.sql.column('dbnode_id', sa.Integer),
        sa.sql.column('user_id', sa.Integer),
        sa.Column('content', sa.Text),
        sa.Column('ctime', sa.DateTime(timezone=True)),
        sa.Column('mtime', sa.DateTime(timezone=True)),
        sa.Column('uuid', sa.CHAR(32)),
    )

    # remove rows with null values, which may have previously resulted from deletion of a node or user
    op.execute(db_dbcomment.delete().where(db_dbcomment.c.dbnode_id.is_(None)))  # type: ignore[arg-type]
    op.execute(db_dbcomment.delete().where(db_dbcomment.c.user_id.is_(None)))  # type: ignore[arg-type]

    op.execute(db_dbcomment.update().where(db_dbcomment.c.content.is_(None)).values(content=''))
    op.execute(db_dbcomment.update().where(db_dbcomment.c.ctime.is_(None)).values(ctime=timezone.now()))
    op.execute(db_dbcomment.update().where(db_dbcomment.c.mtime.is_(None)).values(mtime=timezone.now()))

    db_dbcomputer = sa.sql.table(
        'db_dbcomputer',
        sa.Column('description', sa.Text),
        sa.Column('hostname', sa.String(255)),
        sa.Column('metadata', sa.JSON()),
        sa.Column('scheduler_type', sa.String(255)),
        sa.Column('transport_type', sa.String(255)),
        sa.Column('uuid', sa.CHAR(32)),
    )

    op.execute(db_dbcomputer.update().where(db_dbcomputer.c.description.is_(None)).values(description=''))
    op.execute(db_dbcomputer.update().where(db_dbcomputer.c.hostname.is_(None)).values(hostname=''))
    op.execute(db_dbcomputer.update().where(db_dbcomputer.c.metadata.is_(None)).values(metadata={}))
    op.execute(db_dbcomputer.update().where(db_dbcomputer.c.scheduler_type.is_(None)).values(scheduler_type=''))
    op.execute(db_dbcomputer.update().where(db_dbcomputer.c.transport_type.is_(None)).values(transport_type=''))

    db_dbgroup = sa.sql.table(
        'db_dbgroup',
        sa.Column('description', sa.Text),
        sa.Column('label', sa.String(255)),
        sa.Column('time', sa.DateTime(timezone=True)),
        sa.Column('type_string', sa.String(255)),
        sa.Column('uuid', sa.CHAR(32)),
    )

    op.execute(db_dbgroup.update().where(db_dbgroup.c.description.is_(None)).values(description=''))
    op.execute(db_dbgroup.update().where(db_dbgroup.c.time.is_(None)).values(time=timezone.now()))
    op.execute(db_dbgroup.update().where(db_dbgroup.c.type_string.is_(None)).values(type_string='core'))

    db_dblog = sa.sql.table(
        'db_dblog',
        sa.Column('levelname', sa.String(255)),
        sa.Column('loggername', sa.String(255)),
        sa.Column('message', sa.Text),
        sa.Column('metadata', sa.JSON()),
        sa.Column('time', sa.DateTime(timezone=True)),
        sa.Column('uuid', sa.CHAR(32)),
    )

    op.execute(db_dblog.update().where(db_dblog.c.levelname.is_(None)).values(levelname=''))
    op.execute(db_dblog.update().where(db_dblog.c.loggername.is_(None)).values(loggername=''))
    op.execute(db_dblog.update().where(db_dblog.c.message.is_(None)).values(message=''))
    op.execute(db_dblog.update().where(db_dblog.c.metadata.is_(None)).values(metadata={}))
    op.execute(db_dblog.update().where(db_dblog.c.time.is_(None)).values(time=timezone.now()))

    db_dbnode = sa.sql.table(
        'db_dbnode',
        sa.Column('ctime', sa.DateTime(timezone=True)),
        sa.Column('description', sa.Text),
        sa.Column('label', sa.String(255)),
        sa.Column('mtime', sa.DateTime(timezone=True)),
        sa.Column('node_type', sa.String(255)),
        sa.Column('uuid', sa.CHAR(32)),
    )

    op.execute(db_dbnode.update().where(db_dbnode.c.ctime.is_(None)).values(ctime=timezone.now()))
    op.execute(db_dbnode.update().where(db_dbnode.c.description.is_(None)).values(description=''))
    op.execute(db_dbnode.update().where(db_dbnode.c.label.is_(None)).values(label=''))
    op.execute(db_dbnode.update().where(db_dbnode.c.mtime.is_(None)).values(mtime=timezone.now()))

    db_dbuser = sa.sql.table(
        'db_dbuser',
        sa.Column('email', sa.String(254)),
        sa.Column('first_name', sa.String(254)),
        sa.Column('last_name', sa.String(254)),
        sa.Column('institution', sa.String(254)),
    )

    op.execute(db_dbuser.update().where(db_dbuser.c.first_name.is_(None)).values(first_name=''))
    op.execute(db_dbuser.update().where(db_dbuser.c.last_name.is_(None)).values(last_name=''))
    op.execute(db_dbuser.update().where(db_dbuser.c.institution.is_(None)).values(institution=''))


def downgrade():
    """Downgrade database schema."""
    raise NotImplementedError('Downgrade of main_0000a.')
