###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N806
"""Tests for migrations to bring parity between SQLAlchemy and Django."""
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_non_nullable(perform_migrations: PsqlDosMigrator):
    """Test making columns non-nullable."""
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@34a831f4286d')

    # setup the database
    DbAuthInfo = perform_migrations.get_current_table('db_dbauthinfo')
    DbComment = perform_migrations.get_current_table('db_dbcomment')
    DbComputer = perform_migrations.get_current_table('db_dbcomputer')
    DbGroup = perform_migrations.get_current_table('db_dbgroup')
    Dblog = perform_migrations.get_current_table('db_dblog')
    DbNode = perform_migrations.get_current_table('db_dbnode')
    DbSetting = perform_migrations.get_current_table('db_dbsetting')
    DbUser = perform_migrations.get_current_table('db_dbuser')
    with perform_migrations.session() as session:
        setting = DbSetting(key='test_key', val='test_value', description='', time=None)
        session.add(setting)
        user = DbUser(email=None, first_name=None, last_name=None, institution=None)
        session.add(user)
        computer = DbComputer(
            label='computer',
            hostname=None,
            description=None,
            metadata=None,
            scheduler_type=None,
            transport_type=None,
        )
        session.add(computer)
        session.commit()
        setting_id = setting.id
        user_id = user.id
        computer_id = computer.id
        group = DbGroup(label=None, description=None, time=None, type_string=None, extras={}, user_id=user_id)
        session.add(group)
        session.commit()
        group_id = group.id
        authinfo = DbAuthInfo(
            aiidauser_id=user_id, dbcomputer_id=computer_id, enabled=None, auth_params=None, metadata=None
        )
        # this could be the result of a computer being deleted, and should be removed in the migration
        authinfo_dangling = DbAuthInfo(
            aiidauser_id=user_id, dbcomputer_id=None, enabled=None, auth_params=None, metadata=None
        )
        session.add_all([authinfo, authinfo_dangling])
        session.commit()
        authinfo_id = authinfo.id
        authinfo_dangling_id = authinfo_dangling.id
        node = DbNode(
            user_id=user_id,
            ctime=None,
            mtime=None,
            description=None,
            label=None,
            node_type='',
            uuid=None,
            attributes={},
            extras={},
            repository_metadata={},
        )
        session.add(node)
        session.commit()
        node_id = node.id
        comment = DbComment(dbnode_id=node_id, user_id=user_id, content=None, ctime=None, mtime=None, uuid=None)
        session.add(comment)
        session.commit()
        comment_id = comment.id
        log = Dblog(dbnode_id=node_id, levelname='x' * 100)
        session.add(log)
        session.commit()
        log_id = log.id

    # migrate up
    perform_migrations.migrate_up('sqlalchemy@1de112340b18')

    # perform some checks
    DbAuthInfo = perform_migrations.get_current_table('db_dbauthinfo')
    DbComment = perform_migrations.get_current_table('db_dbcomment')
    DbComputer = perform_migrations.get_current_table('db_dbcomputer')
    DbGroup = perform_migrations.get_current_table('db_dbgroup')
    Dblog = perform_migrations.get_current_table('db_dblog')
    DbNode = perform_migrations.get_current_table('db_dbnode')
    DbSetting = perform_migrations.get_current_table('db_dbsetting')
    DbUser = perform_migrations.get_current_table('db_dbuser')
    with perform_migrations.session() as session:
        setting = session.query(DbSetting).filter(DbSetting.id == setting_id).one()
        assert setting.time is not None
        user = session.query(DbUser).filter(DbUser.id == user_id).one()
        assert user.email is not None
        assert user.first_name is not None
        assert user.last_name is not None
        assert user.institution is not None
        computer = session.query(DbComputer).filter(DbComputer.id == computer_id).one()
        assert computer.hostname is not None
        assert computer.description is not None
        assert computer.metadata is not None
        assert computer.scheduler_type is not None
        assert computer.transport_type is not None
        assert computer.uuid is not None
        group = session.query(DbGroup).filter(DbGroup.id == group_id).one()
        assert group.label is not None
        assert group.description is not None
        assert group.time is not None
        assert group.type_string is not None
        assert group.uuid is not None
        authinfo = session.query(DbAuthInfo).filter(DbAuthInfo.id == authinfo_id).one()
        assert authinfo.enabled is not None
        assert authinfo.auth_params is not None
        assert authinfo.metadata is not None
        authinfo_dangling = session.query(DbAuthInfo).filter(DbAuthInfo.id == authinfo_dangling_id).one_or_none()
        assert authinfo_dangling is None
        node = session.query(DbNode).filter(DbNode.id == node_id).one()
        assert node.ctime is not None
        assert node.mtime is not None
        assert node.description is not None
        assert node.label is not None
        assert node.node_type is not None
        assert node.uuid is not None
        comment = session.query(DbComment).filter(DbComment.id == comment_id).one()
        assert comment.content is not None
        assert comment.ctime is not None
        assert comment.mtime is not None
        assert comment.uuid is not None
        log = session.query(Dblog).filter(Dblog.id == log_id).one()
        assert log.uuid is not None
        assert log.time is not None
        assert log.loggername is not None
        assert log.levelname == 'x' * 50
        assert log.message is not None
        assert log.metadata is not None
