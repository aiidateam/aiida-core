"""delete trajectory symbols array

Revision ID: ce56d84bcc35
Revises: 12536798d4d3
Create Date: 2019-01-21 15:35:07.280805

"""
# pylint: disable=invalid-name
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-member,no-name-in-module,import-error

import numpy

from alembic import op
from sqlalchemy.orm.session import Session

from aiida.backends.sqlalchemy.models.node import DbNode
from aiida.backends.sqlalchemy.utils import flag_modified
from aiida.orm import load_node

# revision identifiers, used by Alembic.
revision = 'ce56d84bcc35'
down_revision = '12536798d4d3'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    session = Session(bind=op.get_bind())
    trajectories = session.query(DbNode).filter_by(type='node.data.array.trajectory.TrajectoryData.').all()
    for t in trajectories:
        del t.attributes['array|symbols']
        flag_modified(t, 'attributes')
        load_node(pk=t.id).delete_object('symbols.npy', force=True)
        session.add(t)
    session.commit()
    session.close()


def downgrade():
    """Migrations for the downgrade."""
    import tempfile
    session = Session(bind=op.get_bind())
    trajectories = session.query(DbNode).filter_by(type='node.data.array.trajectory.TrajectoryData.').all()
    for t in trajectories:
        symbols = numpy.array(t.get_attribute('symbols'))
        # Save the .npy file (using set_array raises ModificationNotAllowed error)
        with tempfile.NamedTemporaryFile() as handle:
            numpy.save(handle, symbols)
            handle.flush()
            handle.seek(0)
            load_node(pk=t.id).put_object_from_filelike(handle, 'symbols.npy')
        t.attributes['array|symbols'] = list(symbols.shape)
        flag_modified(t, 'attributes')
        session.add(t)
    session.commit()
    session.close()
