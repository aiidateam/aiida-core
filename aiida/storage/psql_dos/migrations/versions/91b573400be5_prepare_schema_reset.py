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
"""Prepare schema reset.

This is similar to migration django_0042

Revision ID: 91b573400be5
Revises: 7b38a9e783e7
Create Date: 2019-07-25 14:58:39.866822

"""

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '91b573400be5'
down_revision = '7b38a9e783e7'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    # The following statement is trying to perform an UPSERT, i.e. an UPDATE of a given key or if it doesn't exist fall
    # back to an INSERT. This problem is notoriously difficult to solve as explained in great detail in this article:
    # https://www.depesz.com/2012/06/10/why-is-upsert-so-complicated/ Postgres 9.5 provides an offical UPSERT method
    # through the `ON CONFLICT` keyword, but since we also support 9.4 we cannot use it here. The snippet used below
    # taken from the provided link, is not safe for concurrent operations, but since our migrations always run in an
    # isolated way, we do not suffer from those problems and can safely use it.
    statement = text(
        """
        INSERT INTO db_dbsetting (key, val, description)
        SELECT 'schema_generation', '"1"', 'Database schema generation'
        WHERE NOT EXISTS (SELECT * FROM db_dbsetting WHERE key = 'schema_generation');
        """
    )
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of 91b573400be5.')
