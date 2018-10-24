# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Delete the kombu tables that were used by the old Celery based daemon and the obsolete related timestamps

Revision ID: f9a69de76a9a
Revises: 6c629c886f84
Create Date: 2018-05-10 15:07:59.235950

"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from alembic import op
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = 'f9a69de76a9a'
down_revision = '6c629c886f84'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Drop the kombu tables and delete the old timestamps and user related to the daemon in the DbSetting table
    statement = text("""
            DROP TABLE IF EXISTS kombu_message;
            DROP TABLE IF EXISTS kombu_queue;
            DROP SEQUENCE IF EXISTS message_id_sequence;
            DROP SEQUENCE IF EXISTS queue_id_sequence;
            DELETE FROM db_dbsetting WHERE key = 'daemon|user';
            DELETE FROM db_dbsetting WHERE key = 'daemon|task_stop|retriever';
            DELETE FROM db_dbsetting WHERE key = 'daemon|task_start|retriever';
            DELETE FROM db_dbsetting WHERE key = 'daemon|task_stop|updater';
            DELETE FROM db_dbsetting WHERE key = 'daemon|task_start|updater';
            DELETE FROM db_dbsetting WHERE key = 'daemon|task_stop|submitter';
            DELETE FROM db_dbsetting WHERE key = 'daemon|task_start|submitter';
    """)
    conn.execute(statement)


def downgrade():
    print('There is no downgrade for the deletion of the kombu tables and the daemon timestamps')
