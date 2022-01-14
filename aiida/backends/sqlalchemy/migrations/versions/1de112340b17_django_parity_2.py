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
"""Parity with Django backend (rev: 0048),
part 2: Alter columns to be non-nullable and change type of some columns.

Revision ID: 1de112340b17
Revises: 1de112340b16
Create Date: 2021-08-25 04:28:52.102767

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = '1de112340b17'
down_revision = '1de112340b16'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema."""
    op.alter_column('db_dbauthinfo', 'aiidauser_id', existing_type=sa.INTEGER(), nullable=False)
    op.alter_column('db_dbauthinfo', 'dbcomputer_id', existing_type=sa.INTEGER(), nullable=False)
    op.alter_column('db_dbauthinfo', 'metadata', existing_type=JSONB, nullable=False)
    op.alter_column('db_dbauthinfo', 'auth_params', existing_type=JSONB, nullable=False)
    op.alter_column('db_dbauthinfo', 'enabled', existing_type=sa.BOOLEAN(), nullable=False)

    op.alter_column('db_dbcomment', 'dbnode_id', existing_type=sa.INTEGER(), nullable=False)
    op.alter_column('db_dbcomment', 'user_id', existing_type=sa.INTEGER(), nullable=False)
    op.alter_column('db_dbcomment', 'content', existing_type=sa.TEXT(), nullable=False)
    op.alter_column('db_dbcomment', 'ctime', existing_type=sa.DateTime(timezone=True), nullable=False)
    op.alter_column('db_dbcomment', 'mtime', existing_type=sa.DateTime(timezone=True), nullable=False)
    op.alter_column('db_dbcomment', 'uuid', existing_type=UUID(as_uuid=True), nullable=False)

    op.alter_column('db_dbcomputer', 'description', existing_type=sa.TEXT(), nullable=False)
    op.alter_column('db_dbcomputer', 'hostname', existing_type=sa.String(255), nullable=False)
    op.alter_column('db_dbcomputer', 'metadata', existing_type=JSONB, nullable=False)
    op.alter_column('db_dbcomputer', 'scheduler_type', existing_type=sa.String(255), nullable=False)
    op.alter_column('db_dbcomputer', 'transport_type', existing_type=sa.String(255), nullable=False)
    op.alter_column('db_dbcomputer', 'uuid', existing_type=UUID(as_uuid=True), nullable=False)

    op.alter_column('db_dbgroup', 'user_id', existing_type=sa.INTEGER(), nullable=False)
    op.alter_column('db_dbgroup', 'description', existing_type=sa.TEXT(), nullable=False)
    op.alter_column('db_dbgroup', 'label', existing_type=sa.String(255), nullable=False)
    op.alter_column('db_dbgroup', 'time', existing_type=sa.DateTime(timezone=True), nullable=False)
    op.alter_column('db_dbgroup', 'type_string', existing_type=sa.String(255), nullable=False)
    op.alter_column('db_dbgroup', 'uuid', existing_type=UUID(as_uuid=True), nullable=False)

    op.alter_column('db_dbgroup_dbnodes', 'dbnode_id', existing_type=sa.INTEGER(), nullable=False)
    op.alter_column('db_dbgroup_dbnodes', 'dbgroup_id', existing_type=sa.INTEGER(), nullable=False)

    op.alter_column('db_dblink', 'type', existing_type=sa.String(255), nullable=False)
    op.alter_column('db_dblink', 'input_id', existing_type=sa.INTEGER(), nullable=False)
    op.alter_column('db_dblink', 'output_id', existing_type=sa.INTEGER(), nullable=False)

    op.alter_column('db_dblog', 'levelname', existing_type=sa.String(255), type_=sa.String(50), nullable=False)
    op.alter_column('db_dblog', 'loggername', existing_type=sa.String(255), nullable=False)
    op.alter_column('db_dblog', 'message', existing_type=sa.TEXT(), nullable=False)
    op.alter_column('db_dblog', 'time', existing_type=sa.DateTime(timezone=True), nullable=False)
    op.alter_column('db_dblog', 'uuid', existing_type=UUID(as_uuid=True), nullable=False)
    op.alter_column('db_dblog', 'metadata', existing_type=JSONB, nullable=False)

    op.alter_column('db_dbnode', 'ctime', existing_type=sa.DateTime(timezone=True), nullable=False)
    op.alter_column('db_dbnode', 'description', existing_type=sa.TEXT(), nullable=False)
    op.alter_column('db_dbnode', 'label', existing_type=sa.String(255), nullable=False)
    op.alter_column('db_dbnode', 'mtime', existing_type=sa.DateTime(timezone=True), nullable=False)
    op.alter_column('db_dbnode', 'node_type', existing_type=sa.String(255), nullable=False)
    op.alter_column('db_dbnode', 'uuid', existing_type=UUID(as_uuid=True), nullable=False)

    op.alter_column('db_dbsetting', 'time', existing_type=sa.DateTime(timezone=True), nullable=False)
    op.alter_column('db_dbsetting', 'key', existing_type=sa.String(255), type_=sa.String(1024), nullable=False)
    op.alter_column('db_dbsetting', 'description', existing_type=sa.String(255), type_=sa.Text(), nullable=False)

    op.alter_column('db_dbuser', 'email', existing_type=sa.String(254), nullable=False)
    op.alter_column('db_dbuser', 'first_name', existing_type=sa.String(254), nullable=False)
    op.alter_column('db_dbuser', 'last_name', existing_type=sa.String(254), nullable=False)
    op.alter_column('db_dbuser', 'institution', existing_type=sa.String(254), nullable=False)


def downgrade():
    """Downgrade database schema."""
    op.alter_column('db_dbuser', 'institution', existing_type=sa.String(254), nullable=True)
    op.alter_column('db_dbuser', 'last_name', existing_type=sa.String(254), nullable=True)
    op.alter_column('db_dbuser', 'first_name', existing_type=sa.String(254), nullable=True)
    op.alter_column('db_dbuser', 'email', existing_type=sa.String(254), nullable=True)

    op.alter_column('db_dbsetting', 'time', existing_type=sa.DateTime(timezone=True), nullable=True)
    op.alter_column('db_dbsetting', 'key', existing_type=sa.String(1024), type_=sa.String(255), nullable=False)
    op.alter_column('db_dbsetting', 'description', existing_type=sa.Text(), type_=sa.String(255), nullable=False)

    op.alter_column('db_dbnode', 'ctime', existing_type=sa.DateTime(timezone=True), nullable=True)
    op.alter_column('db_dbnode', 'description', existing_type=sa.TEXT(), nullable=True)
    op.alter_column('db_dbnode', 'label', existing_type=sa.String(255), nullable=True)
    op.alter_column('db_dbnode', 'mtime', existing_type=sa.DateTime(timezone=True), nullable=True)
    op.alter_column('db_dbnode', 'node_type', existing_type=sa.String(255), nullable=True)
    op.alter_column('db_dbnode', 'uuid', existing_type=UUID(as_uuid=True), nullable=True)

    op.alter_column('db_dblog', 'metadata', existing_type=JSONB, nullable=True)
    op.alter_column('db_dblog', 'message', existing_type=sa.TEXT(), nullable=True)
    op.alter_column('db_dblog', 'levelname', existing_type=sa.String(50), type_=sa.String(255), nullable=True)
    op.alter_column('db_dblog', 'loggername', existing_type=sa.String(255), nullable=True)
    op.alter_column('db_dblog', 'time', existing_type=sa.DateTime(timezone=True), nullable=True)
    op.alter_column('db_dblog', 'uuid', existing_type=UUID(as_uuid=True), nullable=True)

    op.alter_column('db_dblink', 'output_id', existing_type=sa.INTEGER(), nullable=True)
    op.alter_column('db_dblink', 'input_id', existing_type=sa.INTEGER(), nullable=True)
    op.alter_column('db_dblink', 'type', existing_type=sa.String(255), nullable=True)

    op.alter_column('db_dbgroup_dbnodes', 'dbgroup_id', existing_type=sa.INTEGER(), nullable=True)
    op.alter_column('db_dbgroup_dbnodes', 'dbnode_id', existing_type=sa.INTEGER(), nullable=True)

    op.alter_column('db_dbgroup', 'user_id', existing_type=sa.INTEGER(), nullable=True)
    op.alter_column('db_dbgroup', 'description', existing_type=sa.TEXT(), nullable=True)
    op.alter_column('db_dbgroup', 'time', existing_type=sa.DateTime(timezone=True), nullable=True)
    op.alter_column('db_dbgroup', 'type_string', existing_type=sa.String(255), nullable=True)
    op.alter_column('db_dbgroup', 'label', existing_type=sa.String(255), nullable=True)
    op.alter_column('db_dbgroup', 'uuid', existing_type=UUID(as_uuid=True), nullable=True)

    op.alter_column('db_dbcomputer', 'metadata', existing_type=JSONB, nullable=True)
    op.alter_column('db_dbcomputer', 'transport_type', existing_type=sa.String(255), nullable=True)
    op.alter_column('db_dbcomputer', 'scheduler_type', existing_type=sa.String(255), nullable=True)
    op.alter_column('db_dbcomputer', 'description', existing_type=sa.TEXT(), nullable=True)
    op.alter_column('db_dbcomputer', 'hostname', existing_type=sa.String(255), nullable=True)
    op.alter_column('db_dbcomputer', 'uuid', existing_type=UUID(as_uuid=True), nullable=True)

    op.alter_column('db_dbcomment', 'user_id', existing_type=sa.INTEGER(), nullable=True)
    op.alter_column('db_dbcomment', 'dbnode_id', existing_type=sa.INTEGER(), nullable=True)
    op.alter_column('db_dbcomment', 'content', existing_type=sa.TEXT(), nullable=True)
    op.alter_column('db_dbcomment', 'ctime', existing_type=sa.DateTime(timezone=True), nullable=True)
    op.alter_column('db_dbcomment', 'mtime', existing_type=sa.DateTime(timezone=True), nullable=True)
    op.alter_column('db_dbcomment', 'uuid', existing_type=UUID(as_uuid=True), nullable=True)

    op.alter_column('db_dbauthinfo', 'dbcomputer_id', existing_type=sa.INTEGER(), nullable=True)
    op.alter_column('db_dbauthinfo', 'aiidauser_id', existing_type=sa.INTEGER(), nullable=True)
    op.alter_column('db_dbauthinfo', 'enabled', existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column('db_dbauthinfo', 'auth_params', existing_type=JSONB, nullable=True)
    op.alter_column('db_dbauthinfo', 'metadata', existing_type=JSONB, nullable=True)
