###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the ORM Backend class."""

from __future__ import annotations

import json
import pathlib
import uuid

import pytest

from aiida import orm
from aiida.common import exceptions
from aiida.common.links import LinkType
from aiida.orm.entities import EntityTypes


class TestBackend:
    """Test backend."""

    @pytest.fixture(autouse=True)
    def init_test(self, backend):
        """Set up the backend."""
        self.backend = backend

    def test_transaction_nesting(self):
        """Test that transaction nesting works."""
        user = orm.User('initial@email.com').store()
        with self.backend.transaction():
            user.email = 'pre-failure@email.com'
            try:
                with self.backend.transaction():
                    user.email = 'failure@email.com'
                    assert user.email == 'failure@email.com'
                    raise RuntimeError
            except RuntimeError:
                pass
            assert user.email == 'pre-failure@email.com'
        assert user.email == 'pre-failure@email.com'

    def test_transaction(self):
        """Test that transaction nesting works."""
        user1 = orm.User('user1@email.com').store()
        user2 = orm.User('user2@email.com').store()

        try:
            with self.backend.transaction():
                assert self.backend.in_transaction
                user1.email = 'broken1@email.com'
                user2.email = 'broken2@email.com'
                raise RuntimeError
        except RuntimeError:
            pass
        assert user1.email == 'user1@email.com'
        assert user2.email == 'user2@email.com'

    def test_store_in_transaction(self):
        """Test that storing inside a transaction is correctly dealt with."""
        user1 = orm.User('user_store@email.com')
        with self.backend.transaction():
            user1.store()
        # the following shouldn't raise
        orm.User.collection.get(email='user_store@email.com')

        user2 = orm.User('user_store_fail@email.com')
        try:
            with self.backend.transaction():
                user2.store()
                raise RuntimeError
        except RuntimeError:
            pass

        with pytest.raises(exceptions.NotExistent):
            orm.User.collection.get(email='user_store_fail@email.com')

    def test_bulk_insert(self):
        """Test that bulk insert works."""
        rows = [{'email': uuid.uuid4().hex}, {'email': uuid.uuid4().hex}]
        # should fail if all fields are not given and allow_defaults=False
        with pytest.raises(exceptions.IntegrityError, match='Incorrect fields'):
            self.backend.bulk_insert(EntityTypes.USER, rows)
        pks = self.backend.bulk_insert(EntityTypes.USER, rows, allow_defaults=True)
        assert len(pks) == len(rows)
        for pk, row in zip(pks, rows):
            assert isinstance(pk, int)
            user = orm.User.collection.get(id=pk)
            assert user.email == row['email']

    def test_bulk_insert_in_transaction(self):
        """Test that bulk insert in a cancelled transaction is not committed."""
        rows = [{'email': uuid.uuid4().hex}, {'email': uuid.uuid4().hex}]
        try:
            with self.backend.transaction():
                self.backend.bulk_insert(EntityTypes.USER, rows, allow_defaults=True)
                raise RuntimeError
        except RuntimeError:
            pass
        for row in rows:
            with pytest.raises(exceptions.NotExistent):
                orm.User.collection.get(email=row['email'])

    def test_bulk_update(self):
        """Test that bulk update works."""
        prefix = uuid.uuid4().hex
        users = [orm.User(f'{prefix}-{i}').store() for i in range(3)]
        # should raise if the 'id' field is not present
        with pytest.raises(exceptions.IntegrityError, match="'id' field not given"):
            self.backend.bulk_update(EntityTypes.USER, [{'email': 'other'}])
        # should raise if a non-existent field is present
        with pytest.raises(exceptions.IntegrityError, match='Incorrect fields'):
            self.backend.bulk_update(EntityTypes.USER, [{'id': users[0].pk, 'x': 'other'}])
        self.backend.bulk_update(
            EntityTypes.USER, [{'id': users[0].pk, 'email': 'other0'}, {'id': users[1].pk, 'email': 'other1'}]
        )
        assert users[0].email == 'other0'
        assert users[1].email == 'other1'
        assert users[2].email == f'{prefix}-2'

    def test_bulk_update_in_transaction(self):
        """Test that bulk update in a cancelled transaction is not committed."""
        prefix = uuid.uuid4().hex
        users = [orm.User(f'{prefix}-{i}').store() for i in range(3)]
        try:
            with self.backend.transaction():
                self.backend.bulk_update(
                    EntityTypes.USER, [{'id': users[0].pk, 'email': 'random0'}, {'id': users[1].pk, 'email': 'random1'}]
                )
                raise RuntimeError
        except RuntimeError:
            pass
        for i, user in enumerate(users):
            assert user.email == f'{prefix}-{i}'

    def test_delete_nodes_and_connections(self):
        """Delete all nodes and connections."""
        # create node, link and add to group
        node = orm.Data()
        calc_node = orm.CalcFunctionNode().store()
        node.base.links.add_incoming(calc_node, link_type=LinkType.CREATE, link_label='link')
        node.store()
        node_pk = node.pk
        group = orm.Group('name').store()
        group.add_nodes([node])

        # checks before deletion
        orm.Node.collection.get(id=node_pk)
        assert len(calc_node.base.links.get_outgoing().all()) == 1
        assert len(group.nodes) == 1

        # cannot call outside a transaction
        with pytest.raises(AssertionError):
            self.backend.delete_nodes_and_connections([node_pk])

        with self.backend.transaction():
            self.backend.delete_nodes_and_connections([node_pk])

        # checks after deletion
        with pytest.raises(exceptions.NotExistent):
            orm.Node.collection.get(id=node_pk)
        assert len(calc_node.base.links.get_outgoing().all()) == 0
        assert len(group.nodes) == 0


def test_backup_not_implemented(aiida_config, backend, monkeypatch, tmp_path):
    """Test the backup functionality if the plugin does not implement it."""

    def _backup(*args, **kwargs):
        raise NotImplementedError

    monkeypatch.setattr(backend, '_backup', _backup)

    filepath_backup = tmp_path / 'backup_dir'

    with pytest.raises(NotImplementedError):
        backend.backup(str(filepath_backup))

    # The backup directory should have been initialized but then cleaned up when the plugin raised the exception
    assert not filepath_backup.is_dir()

    # Now create the backup directory with the config file and some other content to it.
    filepath_backup.mkdir()
    (filepath_backup / 'config.json').write_text(json.dumps(aiida_config.dictionary))
    (filepath_backup / 'backup-deadbeef').mkdir()

    with pytest.raises(NotImplementedError):
        backend.backup(str(filepath_backup))

    # The backup directory should not have been delete
    assert filepath_backup.is_dir()
    assert (filepath_backup / 'config.json').is_file()


def test_backup_implemented(backend, monkeypatch, tmp_path):
    """Test the backup functionality if the plugin does implement it."""

    def _backup(dest: str, keep: int | None = None):
        (pathlib.Path(dest) / 'backup.file').touch()

    monkeypatch.setattr(backend, '_backup', _backup)

    filepath_backup = tmp_path / 'backup_dir'
    backend.backup(str(filepath_backup))
    assert (filepath_backup / 'config.json').is_file()
    assert (filepath_backup / 'backup.file').is_file()
