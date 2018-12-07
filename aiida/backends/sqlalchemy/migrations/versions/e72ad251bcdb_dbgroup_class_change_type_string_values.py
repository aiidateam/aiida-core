"""DbGroup class: change type_string values

Revision ID: e72ad251bcdb
Revises: b8b23ddefad4
Create Date: 2018-12-06 19:34:47.732890

"""
from __future__ import absolute_import
from alembic import op
from sqlalchemy.sql import text

forward_sql = [
    """UPDATE db_dbgroup SET type_string = 'user' WHERE type_string = '';""",
    """UPDATE db_dbgroup SET type_string = 'data.upf' WHERE type_string = 'data.upf.family';""",
    """UPDATE db_dbgroup SET type_string = 'auto.import' WHERE type_string = 'aiida.import';""",
    """UPDATE db_dbgroup SET type_string = 'auto.run' WHERE type_string = 'autogroup.run';""",
]

reverse_sql = [
    """UPDATE db_dbgroup SET type_string = '' WHERE type_string = 'user';""",
    """UPDATE db_dbgroup SET type_string = 'data.upf.family' WHERE type_string = 'data.upf';""",
    """UPDATE db_dbgroup SET type_string = 'aiida.import' WHERE type_string = 'auto.import';""",
    """UPDATE db_dbgroup SET type_string = 'autogroup.run' WHERE type_string = 'auto.run';""",
]

# revision identifiers, used by Alembic.
revision = 'e72ad251bcdb'
down_revision = 'b8b23ddefad4'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    statement = text('\n'.join(forward_sql))
    conn.execute(statement)


def downgrade():
    conn = op.get_bind()
    statement = text('\n'.join(reverse_sql))
    conn.execute(statement)
