"""create account table

Revision ID: 470e57bc0936
Revises: 
Create Date: 2017-06-16 17:53:10.920345

"""
from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy.models.settings import DbSetting

# revision identifiers, used by Alembic.
revision = '470e57bc0936'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Delete the old schema version
    sa.get_scoped_session().query(DbSetting).filter(
        DbSetting.key == "db|schemaversion").delete()


def downgrade():
    #  Add the old schema version
    DbSetting.set_value('db|schemaversion', '0.1', other_attribs={
        "description": 'The version of the schema used in this database.'})
