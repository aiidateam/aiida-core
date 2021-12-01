# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.backends.control` module."""
import pytest

from aiida.manage.manager import get_manager


class MockRepositoryBackend():
    """Mock of the RepositoryBackend for testing purposes."""

    # pylint: disable=no-self-use

    def get_info(self, *args, **kwargs):
        """Method to return information."""
        return 'this is information about the repo'

    def delete_objects(self, *args, **kwargs):
        """Method to delete objects."""

    def maintain(self, full=False, **kwargs):
        """Method to perform maintainance operations."""
        text = 'this is a report on the maintenance procedure'
        if full:
            text += ' with the full flag on'
        return text


@pytest.fixture(scope='function')
@pytest.mark.usefixtures('clear_database_before_test')
def clear_storage_before_test():
    """Clears the storage before a test."""
    repository = get_manager().get_backend().get_repository()
    object_keys = list(repository.list_objects())
    repository.delete_objects(object_keys)
    repository.maintain(full=True)


@pytest.mark.usefixtures('clear_database_before_test', 'clear_storage_before_test')
def test_get_unreferenced_keyset():
    """Test the ``get_unreferenced_keyset`` method."""
    # NOTE: This tests needs to use the database because there is a call inside
    # `get_unreferenced_keyset` that would require to mock a very complex class
    # structure:
    #
    #     keyset_aiidadb = set(orm.Node.objects(aiida_backend).iter_repo_keys())
    #
    # Ideally this should eventually be replaced by a more direct call to the
    # method of a single object that would be easier to mock and would allow
    # to unit-test this in isolation.
    from io import BytesIO

    from aiida import orm
    from aiida.backends.control import get_unreferenced_keyset

    # Coverage code pass
    unreferenced_keyset = get_unreferenced_keyset()
    assert unreferenced_keyset == set()

    # Error catching: put a file, get the keys from the aiida db, manually delete the keys
    # in the repository
    datanode = orm.FolderData()
    datanode.put_object_from_filelike(BytesIO(b'File content'), 'file.txt')
    datanode.store()

    aiida_backend = get_manager().get_backend()
    keys = list(orm.Node.objects(aiida_backend).iter_repo_keys())

    repository_backend = aiida_backend.get_repository()
    repository_backend.delete_objects(keys)

    with pytest.raises(
        RuntimeError, match='There are objects referenced in the database that are not present in the repository'
    ) as exc:
        get_unreferenced_keyset()
    assert 'aborting' in str(exc.value).lower()


def test_repository_maintain(monkeypatch):
    """Test the ``repository_maintain`` method."""
    from aiida.backends import control
    monkeypatch.setattr(control, 'get_unreferenced_keyset', lambda **kwargs: set([1, 2, 3]))

    BackendClass = get_manager().get_backend().__class__  # pylint: disable=invalid-name
    monkeypatch.setattr(BackendClass, 'get_repository', lambda *args, **kwargs: MockRepositoryBackend())

    final_data = control.repository_maintain()
    assert 'database' in final_data
    assert 'repository' in final_data
    assert 'user_info' in final_data

    assert final_data['repository']['info'] == 'this is information about the repo'
    assert final_data['repository']['maintain'] == 'this is a report on the maintenance procedure'
    assert final_data['repository']['unreferenced'] == 3

    final_data = control.repository_maintain(full=True)
    assert final_data['repository']['maintain'] == 'this is a report on the maintenance procedure with the full flag on'


def test_repository_info(monkeypatch):
    """Test the ``repository_info`` method."""
    from aiida.backends.control import get_repository_info

    def mock_get_info(self, statistics=False, **kwargs):  # pylint: disable=unused-argument
        text = 'Info from repo'
        if statistics:
            text += ' with statistics'
        return text

    RepositoryClass = get_manager().get_backend().get_repository().__class__  # pylint: disable=invalid-name
    monkeypatch.setattr(RepositoryClass, 'get_info', mock_get_info)

    repository_info_out = get_repository_info()
    assert 'Info from repo' in repository_info_out

    repository_info_out = get_repository_info(statistics=True)
    assert 'with statistics' in repository_info_out


def test_get_repository_report(monkeypatch):
    """Test the ``get_repository_report`` method."""
    from aiida.backends import control

    monkeypatch.setattr(control, 'get_unreferenced_keyset', lambda **kwargs: set())

    repository_report = control.get_repository_report()

    assert 'user_info' in repository_report
    assert 'Unreferenced files to delete' in repository_report['user_info']
