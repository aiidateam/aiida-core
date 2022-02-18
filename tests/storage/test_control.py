# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.storage.control` module."""
import pytest

from aiida.manage import get_manager


class MockRepositoryBackend():
    """Mock of the RepositoryBackend for testing purposes."""

    # pylint: disable=no-self-use

    def get_info(self, *args, **kwargs):  # pylint: disable=unused-argument
        """Method to return information."""
        return 'this is information about the repo'

    def delete_objects(self, *args, **kwargs):  # pylint: disable=unused-argument
        """Method to delete objects."""

    def maintain(self, live=True, dry_run=False, **kwargs):
        """Method to perform maintainance operations."""

        if live:
            raise ValueError('Signal that live=True')

        elif dry_run:
            raise ValueError('Signal that dry_run=True')

        elif len(kwargs) > 0:
            raise ValueError('Signal that kwargs were passed')

        else:
            raise ValueError('Signal that live and dry_run are False')


@pytest.fixture(scope='function')
def clear_storage_before_test(aiida_profile_clean):  # pylint: disable=unused-argument
    """Clears the storage before a test."""
    repository = get_manager().get_profile_storage().get_repository()
    object_keys = list(repository.list_objects())
    repository.delete_objects(object_keys)
    repository.maintain(live=False)


@pytest.mark.usefixtures('clear_storage_before_test')
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
    from aiida.storage.control import get_unreferenced_keyset

    # Coverage code pass
    unreferenced_keyset = get_unreferenced_keyset()
    assert unreferenced_keyset == set()

    # Error catching: put a file, get the keys from the aiida db, manually delete the keys
    # in the repository
    datanode = orm.FolderData()
    datanode.put_object_from_filelike(BytesIO(b'File content'), 'file.txt')
    datanode.store()

    aiida_backend = get_manager().get_profile_storage()
    keys = list(orm.Node.objects(aiida_backend).iter_repo_keys())

    repository_backend = aiida_backend.get_repository()
    repository_backend.delete_objects(keys)

    with pytest.raises(
        RuntimeError, match='There are objects referenced in the database that are not present in the repository'
    ) as exc:
        get_unreferenced_keyset()
    assert 'aborting' in str(exc.value).lower()


#yapf: disable
@pytest.mark.parametrize(('kwargs', 'logged_texts'), (
    (
        {},
        [' > live: True', ' > dry_run: False']
    ),
    (
        {'full': True, 'dry_run': True},
        [' > live: False', ' > dry_run: True']
    ),
    (
        {'extra_kwarg': 'molly'},
        [' > live: True', ' > dry_run: False', ' > extra_kwarg: molly']
    ),
))
# yapf: enable
@pytest.mark.usefixtures('clear_storage_before_test')
def test_repository_maintain(caplog, monkeypatch, kwargs, logged_texts):
    """Test the ``repository_maintain`` method."""
    import logging

    from aiida.storage.control import repository_maintain

    def mock_maintain(self, live=True, dry_run=False, **kwargs):  # pylint: disable=unused-argument
        logmsg = 'keywords provided:\n'
        logmsg += f' > live: {live}\n'
        logmsg += f' > dry_run: {dry_run}\n'
        for key, val in kwargs.items():
            logmsg += f' > {key}: {val}\n'
        logging.info(logmsg)

    RepoBackendClass = get_manager().get_profile_storage().get_repository().__class__  # pylint: disable=invalid-name
    monkeypatch.setattr(RepoBackendClass, 'maintain', mock_maintain)

    with caplog.at_level(logging.INFO):
        repository_maintain(**kwargs)

    message_list = caplog.records[0].msg.splitlines()
    for text in logged_texts:
        assert text in message_list


def test_repository_info(monkeypatch):
    """Test the ``repository_info`` method."""
    from aiida.storage.control import get_repository_info

    def mock_get_info(self, statistics=False, **kwargs):  # pylint: disable=unused-argument
        output = {'value': 42}
        if statistics:
            output['extra_value'] = 0
        return output

    RepoBackendClass = get_manager().get_profile_storage().get_repository().__class__  # pylint: disable=invalid-name
    monkeypatch.setattr(RepoBackendClass, 'get_info', mock_get_info)

    repository_info_out = get_repository_info()
    assert 'value' in repository_info_out
    assert 'extra_value' not in repository_info_out
    assert repository_info_out['value'] == 42

    repository_info_out = get_repository_info(statistics=True)
    assert 'value' in repository_info_out
    assert 'extra_value' in repository_info_out
    assert repository_info_out['value'] == 42
    assert repository_info_out['extra_value'] == 0
