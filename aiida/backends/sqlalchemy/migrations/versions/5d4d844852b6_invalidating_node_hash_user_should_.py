"""Invalidating node hash - User should rehash nodes for caching

Revision ID: 5d4d844852b6
Revises: 62fe0d36de90
Create Date: 2018-10-26 17:14:33.566670

"""
from __future__ import absolute_import
from alembic import op
from sqlalchemy.sql import text
from aiida.orm.implementation.general.node import _HASH_EXTRA_KEY
from aiida.cmdline.utils.echo import echo_warning

# revision identifiers, used by Alembic.
revision = '5d4d844852b6'
down_revision = '62fe0d36de90'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Invalidate all the hashes & inform the user
    echo_warning("Invalidating all the hashes of all the nodes. " "Please run verdi rehash", bold=True)
    statement = text("""UPDATE db_dbnode SET extras = extras #- '{""" + _HASH_EXTRA_KEY + """}'::text[];""")
    conn.execute(statement)


def downgrade():
    conn = op.get_bind()

    # Invalidate all the hashes & inform the user
    echo_warning("Invalidating all the hashes of all the nodes. " "Please run verdi rehash", bold=True)
    statement = text("""UPDATE db_dbnode SET extras = extras #- '{""" + _HASH_EXTRA_KEY + """}'::text[];""")
    conn.execute(statement)
