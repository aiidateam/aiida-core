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
"""Remove kombu messaging tables

Revision ID: django_0011
Revises: django_0010

"""
from alembic import op

revision = 'django_0011'
down_revision = 'django_0010'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.execute(
        """
        DROP TABLE IF EXISTS kombu_message;
        DROP TABLE IF EXISTS kombu_queue;
        DELETE FROM db_dbsetting WHERE key = 'daemon|user';
        DELETE FROM db_dbsetting WHERE key = 'daemon|task_stop|retriever';
        DELETE FROM db_dbsetting WHERE key = 'daemon|task_start|retriever';
        DELETE FROM db_dbsetting WHERE key = 'daemon|task_stop|updater';
        DELETE FROM db_dbsetting WHERE key = 'daemon|task_start|updater';
        DELETE FROM db_dbsetting WHERE key = 'daemon|task_stop|submitter';
        DELETE FROM db_dbsetting WHERE key = 'daemon|task_start|submitter';
        """
    )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Deletion of the kombu tables is not reversible.')
