"""trajectory symbols to attribute

Revision ID: 12536798d4d3
Revises: 37f3d4882837
Create Date: 2019-01-21 10:15:02.451308

"""
# pylint: disable=invalid-name
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-member,no-name-in-module,import-error

from alembic import op
from sqlalchemy.orm.session import Session

from aiida.backends.sqlalchemy.utils import flag_modified, get_current_table
from aiida.orm import load_node

# revision identifiers, used by Alembic.
revision = '12536798d4d3'
down_revision = '37f3d4882837'
branch_labels = None
depends_on = None

# Here we duplicate the data stored in a TrajectoryData symbols array, storing it as an attribute.
# We delete the duplicates in the following migration (ce56d84bcc35) to avoid to delete data


def upgrade():
    """Migrations for the upgrade."""
    bind = op.get_bind()
    session = Session(bind=bind)

    DbNode = get_current_table(bind, 'db_dbnode')

    trajectories = session.query(DbNode).filter_by(type='node.data.array.trajectory.TrajectoryData.').all()
    for t in trajectories:
        symbols = load_node(pk=t.id).get_array('symbols').tolist()
        t.attributes['symbols'] = symbols
        flag_modified(t, 'attributes')
        session.add(t)
    session.commit()
    session.close()


def downgrade():
    """Migrations for the downgrade."""
    bind = op.get_bind()
    session = Session(bind=bind)

    DbNode = get_current_table(bind, 'db_dbnode')

    trajectories = session.query(DbNode).filter_by(type='node.data.array.trajectory.TrajectoryData.').all()
    for t in trajectories:
        t.delete_attribute('symbols')
        flag_modified(t, 'attributes')
        session.add(t)
    session.commit()
    session.close()
