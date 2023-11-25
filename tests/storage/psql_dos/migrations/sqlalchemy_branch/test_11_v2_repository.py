# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N806
"""Tests for migrations forming the move from aiida-core v1 to v2."""
import hashlib
import os

from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.backend import get_filepath_container
from aiida.storage.psql_dos.migrations.utils import utils
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_node_repository_metadata(perform_migrations: PsqlDosMigrator):
    """Test migration adding the `repository_metadata` column to the `Node` model.

    Verify that the column is added and null by default.
    """
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@0edcdd5a30f0')  # 0edcdd5a30f0_dbgroup_extras.py

    # setup the database
    DbNode = perform_migrations.get_current_table('db_dbnode')
    DbUser = perform_migrations.get_current_table('db_dbuser')
    with perform_migrations.session() as session:
        default_user = DbUser(email='user@aiida.net')
        session.add(default_user)
        session.commit()
        node = DbNode(user_id=default_user.id)
        session.add(node)
        session.commit()

        node_id = node.id

    # migrate up
    perform_migrations.migrate_up('sqlalchemy@7536a82b2cc4')  # 7536a82b2cc4_add_node_repository_metadata.py

    # perform some checks
    DbNode = perform_migrations.get_current_table('db_dbnode')
    with perform_migrations.session() as session:
        node = session.query(DbNode).filter(DbNode.id == node_id).one()
        assert hasattr(node, 'repository_metadata')
        assert node.repository_metadata == {}


def test_entry_point_core_prefix(perform_migrations: PsqlDosMigrator):
    """Test migration that updates node types after `core.` prefix was added to entry point names.

    Verify that the column was successfully renamed.
    """
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@535039300e4a')  # 535039300e4a_computer_name_to_label.py

    # setup the database
    DbComputer = perform_migrations.get_current_table('db_dbcomputer')
    DbNode = perform_migrations.get_current_table('db_dbnode')
    DbUser = perform_migrations.get_current_table('db_dbuser')
    with perform_migrations.session() as session:
        user = DbUser(email='user@aiida.net')
        session.add(user)
        session.commit()

        computer = DbComputer(label='testing', scheduler_type='direct', transport_type='local')
        session.add(computer)
        session.commit()
        computer_id = computer.id

        calcjob = DbNode(
            user_id=user.id,
            process_type='aiida.calculations:core.arithmetic.add',
            attributes={'parser_name': 'core.arithmetic.add'},
            repository_metadata={},
        )
        session.add(calcjob)
        session.commit()
        calcjob_id = calcjob.id

        workflow = DbNode(
            user_id=user.id,
            process_type='aiida.workflows:arithmetic.add_multiply',
            repository_metadata={},
        )
        session.add(workflow)
        session.commit()
        workflow_id = workflow.id

    # migrate up
    perform_migrations.migrate_up('sqlalchemy@34a831f4286d')  # 34a831f4286d_entry_point_core_prefix

    # perform some checks
    DbComputer = perform_migrations.get_current_table('db_dbcomputer')
    DbNode = perform_migrations.get_current_table('db_dbnode')
    with perform_migrations.session() as session:
        computer = session.query(DbComputer).filter(DbComputer.id == computer_id).one()
        assert computer.scheduler_type == 'core.direct'
        assert computer.transport_type == 'core.local'

        calcjob = session.query(DbNode).filter(DbNode.id == calcjob_id).one()
        assert calcjob.process_type == 'aiida.calculations:core.arithmetic.add'
        assert calcjob.attributes['parser_name'] == 'core.arithmetic.add'

        workflow = session.query(DbNode).filter(DbNode.id == workflow_id).one()
        assert workflow.process_type == 'aiida.workflows:core.arithmetic.add_multiply'


def test_repository_migration(perform_migrations: PsqlDosMigrator):
    """Test migration of the old file repository to the disk object store.

    Verify that the files are correctly migrated.
    """
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@7536a82b2cc4')

    # setup the database
    DbNode = perform_migrations.get_current_table('db_dbnode')
    DbUser = perform_migrations.get_current_table('db_dbuser')
    with perform_migrations.session() as session:
        default_user = DbUser(email='user@aiida.net')
        session.add(default_user)
        session.commit()

        node_01 = DbNode(user_id=default_user.id, uuid=get_new_uuid(), repository_metadata={})
        node_02 = DbNode(user_id=default_user.id, uuid=get_new_uuid(), repository_metadata={})
        node_03 = DbNode(user_id=default_user.id, uuid=get_new_uuid(), repository_metadata={})
        node_04 = DbNode(user_id=default_user.id, uuid=get_new_uuid(), repository_metadata={})
        node_05 = DbNode(user_id=default_user.id, uuid=get_new_uuid(), repository_metadata={})

        session.add(node_01)
        session.add(node_02)
        session.add(node_03)  # Empty repository folder
        session.add(node_04)  # Both `path` and `raw_input` subfolder
        session.add(node_05)  # Both `path` and `raw_input` subfolder & `.gitignore` in `path`
        session.commit()

        assert node_01.uuid is not None
        assert node_02.uuid is not None
        assert node_03.uuid is not None
        assert node_04.uuid is not None
        assert node_05.uuid is not None

        node_01_pk = node_01.id
        node_02_pk = node_02.id
        node_03_pk = node_03.id
        node_05_pk = node_05.id

        repo_path = get_filepath_container(perform_migrations.profile).parent

        utils.put_object_from_string(repo_path, node_01.uuid, 'sub/path/file_b.txt', 'b')
        utils.put_object_from_string(repo_path, node_01.uuid, 'sub/file_a.txt', 'a')
        utils.put_object_from_string(repo_path, node_02.uuid, 'output.txt', 'output')

        os.makedirs(utils.get_node_repository_sub_folder(repo_path, node_04.uuid, 'path'), exist_ok=True)
        os.makedirs(utils.get_node_repository_sub_folder(repo_path, node_04.uuid, 'raw_input'), exist_ok=True)
        os.makedirs(utils.get_node_repository_sub_folder(repo_path, node_05.uuid, 'path'), exist_ok=True)
        os.makedirs(utils.get_node_repository_sub_folder(repo_path, node_05.uuid, 'raw_input'), exist_ok=True)

        utils.put_object_from_string(repo_path, node_05.uuid, '.gitignore', 'test')
        with open(
            os.path.join(utils.get_node_repository_sub_folder(repo_path, node_05.uuid, 'raw_input'), 'input.txt'),
            'w',
            encoding='utf-8',
        ) as handle:
            handle.write('input')

        # Add a repository folder for a node that no longer exists - i.e. it may have been deleted.
        utils.put_object_from_string(repo_path, get_new_uuid(), 'file_of_deleted_node', 'output')

    # migrate up
    perform_migrations.migrate_up('sqlalchemy@1feaea71bd5a')

    # perform some checks
    repository_uuid_key = 'repository|uuid'
    DbNode = perform_migrations.get_current_table('db_dbnode')
    DbSetting = perform_migrations.get_current_table('db_dbsetting')
    with perform_migrations.session() as session:
        node_01 = session.query(DbNode).filter(DbNode.id == node_01_pk).one()
        node_02 = session.query(DbNode).filter(DbNode.id == node_02_pk).one()
        node_03 = session.query(DbNode).filter(DbNode.id == node_03_pk).one()
        node_05 = session.query(DbNode).filter(DbNode.id == node_05_pk).one()

        assert node_01.repository_metadata == {
            'o': {
                'sub': {
                    'o': {
                        'path': {'o': {'file_b.txt': {'k': hashlib.sha256('b'.encode('utf-8')).hexdigest()}}},
                        'file_a.txt': {'k': hashlib.sha256('a'.encode('utf-8')).hexdigest()},
                    }
                }
            }
        }
        assert node_02.repository_metadata == {
            'o': {'output.txt': {'k': hashlib.sha256('output'.encode('utf-8')).hexdigest()}}
        }
        assert node_03.repository_metadata == {}
        assert node_05.repository_metadata == {
            'o': {'input.txt': {'k': hashlib.sha256('input'.encode('utf-8')).hexdigest()}}
        }

        for hashkey, content in (
            (node_01.repository_metadata['o']['sub']['o']['path']['o']['file_b.txt']['k'], b'b'),
            (node_01.repository_metadata['o']['sub']['o']['file_a.txt']['k'], b'a'),
            (node_02.repository_metadata['o']['output.txt']['k'], b'output'),
            (node_05.repository_metadata['o']['input.txt']['k'], b'input'),
        ):
            assert utils.get_repository_object(perform_migrations.profile, hashkey) == content

        repository_uuid = session.query(DbSetting).filter(DbSetting.key == repository_uuid_key).one()
        assert repository_uuid is not None
        assert isinstance(repository_uuid.val, str)


def test_computer_name_to_label(perform_migrations: PsqlDosMigrator):
    """Test the renaming of `name` to `label` for `DbComputer.

    Verify that the column was successfully renamed.
    """
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@1feaea71bd5a')  # 1feaea71bd5a_migrate_repository

    # setup the database
    DbComputer = perform_migrations.get_current_table('db_dbcomputer')
    with perform_migrations.session() as session:
        computer = DbComputer(name='testing')
        session.add(computer)
        session.commit()
        computer_id = computer.id

    # migrate up
    perform_migrations.migrate_up('sqlalchemy@535039300e4a')  # 5ddd24e52864_dbnode_type_to_dbnode_node_type

    # perform some checks
    DbComputer = perform_migrations.get_current_table('db_dbcomputer')
    with perform_migrations.session() as session:
        computer = session.query(DbComputer).filter(DbComputer.id == computer_id).one()
        assert computer.label == 'testing'
