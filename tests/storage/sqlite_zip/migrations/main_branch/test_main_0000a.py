###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test ``main_0000a_replace_nulls.py``."""

from pathlib import Path

from alembic.command import upgrade
from sqlalchemy.orm import Session

from aiida.storage.sqlite_zip.migrations import v1_db_schema as v1_schema
from aiida.storage.sqlite_zip.migrator import _alembic_connect, _migration_context
from aiida.storage.sqlite_zip.utils import create_sqla_engine


def test_migration(null_content_database: Path):
    """Test the migration replaces ``NULL`` values and removes orphaned rows."""
    with _alembic_connect(null_content_database, enforce_foreign_keys=False) as config:
        upgrade(config, 'main_0000a')

    with _migration_context(null_content_database) as context:
        assert context.get_current_revision() == 'main_0000a'

    engine = create_sqla_engine(null_content_database)
    with Session(engine) as session:
        user = session.query(v1_schema.DbUser).one()
        assert (user.first_name, user.last_name, user.institution) == ('', '', '')

        computer = session.query(v1_schema.DbComputer).one()
        assert computer.hostname == ''
        assert computer.description == ''
        assert computer.scheduler_type == ''
        assert computer.transport_type == ''
        assert computer._metadata == {}

        # The orphaned rows are removed, only the valid row remains with replaced values.
        authinfo = session.query(v1_schema.DbAuthInfo).all()
        assert len(authinfo) == 1
        assert authinfo[0].enabled is True
        assert authinfo[0].auth_params == {}
        assert authinfo[0]._metadata == {}

        comments = session.query(v1_schema.DbComment).all()
        assert len(comments) == 1
        assert comments[0].content == ''
        assert comments[0].ctime is not None
        assert comments[0].mtime is not None

        group = session.query(v1_schema.DbGroup).one()
        assert group.type_string == 'core'
        assert group.time is not None
        assert group.description == ''

        log = session.query(v1_schema.DbLog).one()
        assert log.time is not None
        assert log.loggername == ''
        assert log.levelname == ''
        assert log.message == ''
        assert log._metadata == {}

        node = session.query(v1_schema.DbNode).one()
        assert node.label == ''
        assert node.description == ''
        assert node.ctime is not None
        assert node.mtime is not None
