###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Testing the general methods of the psql_dos backend."""

import pytest
from aiida.manage import get_manager
from aiida.orm import User


@pytest.mark.usefixtures('aiida_profile_clean')
def test_default_user():
    assert isinstance(get_manager().get_profile_storage().default_user, User)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_get_unreferenced_keyset():
    """Test the ``get_unreferenced_keyset`` method."""
    # NOTE: This tests needs to use the database because there is a call inside
    # `get_unreferenced_keyset` that would require to mock a very complex class
    # structure:
    #
    #     keyset_aiidadb = set(orm.Node.collection(aiida_backend).iter_repo_keys())
    #
    # Ideally this should eventually be replaced by a more direct call to the
    # method of a single object that would be easier to mock and would allow
    # to unit-test this in isolation.
    from io import BytesIO

    from aiida import orm

    storage_backend = get_manager().get_profile_storage()

    # Coverage code pass
    unreferenced_keyset = storage_backend.get_unreferenced_keyset()
    assert unreferenced_keyset == set()

    # Error catching: put a file, get the keys from the aiida db, manually delete the keys
    # in the repository
    datanode = orm.FolderData()
    datanode.base.repository.put_object_from_filelike(BytesIO(b'File content'), 'file.txt')
    datanode.store()

    aiida_backend = get_manager().get_profile_storage()
    keys = list(orm.Node.collection(aiida_backend).iter_repo_keys())

    repository_backend = aiida_backend.get_repository()
    repository_backend.delete_objects(keys)

    expected_error = 'There are objects referenced in the database that are not present in the repository'
    with pytest.raises(RuntimeError, match=expected_error) as exc:
        storage_backend.get_unreferenced_keyset()
    assert 'aborting' in str(exc.value).lower()


@pytest.mark.parametrize(
    ('kwargs', 'logged_texts'),
    (
        ({}, [' > live: True', ' > dry_run: False', ' > compress: False']),
        ({'full': True, 'dry_run': True}, [' > live: False', ' > dry_run: True', ' > compress: False']),
        (
            {'full': True, 'dry_run': True, 'compress': True},
            [' > live: False', ' > dry_run: True', ' > compress: True'],
        ),
        ({'extra_kwarg': 'molly'}, [' > live: True', ' > dry_run: False', ' > extra_kwarg: molly']),
    ),
)
@pytest.mark.usefixtures('aiida_profile_clean', 'stopped_daemon_client')
def test_maintain(caplog, monkeypatch, kwargs, logged_texts):
    """Test the ``maintain`` method."""
    import logging

    storage_backend = get_manager().get_profile_storage()

    def mock_maintain(self, live=True, dry_run=False, compress=False, **kwargs):
        logmsg = 'keywords provided:\n'
        logmsg += f' > live: {live}\n'
        logmsg += f' > dry_run: {dry_run}\n'
        logmsg += f' > compress: {compress}\n'
        for key, val in kwargs.items():
            logmsg += f' > {key}: {val}\n'
        logging.info(logmsg)

    RepoBackendClass = get_manager().get_profile_storage().get_repository().__class__  # noqa: N806
    monkeypatch.setattr(RepoBackendClass, 'maintain', mock_maintain)

    with caplog.at_level(logging.INFO):
        storage_backend.maintain(**kwargs)

    message_list = caplog.records[0].msg.splitlines()
    for text in logged_texts:
        assert text in message_list


def test_get_info(monkeypatch):
    """Test the ``get_info`` method."""
    storage_backend = get_manager().get_profile_storage()

    def mock_get_info(self, detailed=False, **kwargs):
        output = {'value': 42}
        if detailed:
            output['extra_value'] = 0
        return output

    RepoBackendClass = get_manager().get_profile_storage().get_repository().__class__  # noqa: N806
    monkeypatch.setattr(RepoBackendClass, 'get_info', mock_get_info)

    storage_info_out = storage_backend.get_info()
    assert 'entities' in storage_info_out
    assert 'repository' in storage_info_out

    repository_info_out = storage_info_out['repository']
    assert 'value' in repository_info_out
    assert 'extra_value' not in repository_info_out
    assert repository_info_out['value'] == 42

    storage_info_out = storage_backend.get_info(detailed=True)
    repository_info_out = storage_info_out['repository']
    assert 'value' in repository_info_out
    assert 'extra_value' in repository_info_out
    assert repository_info_out['value'] == 42
    assert repository_info_out['extra_value'] == 0


def test_unload_profile():
    """Test that unloading the profile closes all sqla sessions.

    This is a regression test for #5506.
    """
    import gc

    from sqlalchemy.orm.session import _sessions

    # Run the garbage collector to ensure any lingering unrelated sessions do not cause the test to fail.
    gc.collect()

    # Just running the test suite itself should have opened at least one session
    current_sessions = len(_sessions)
    assert current_sessions != 0, str(_sessions)

    manager = get_manager()
    profile_name = manager.get_profile().name

    try:
        manager.unload_profile()
        # After unloading, the session should have been cleared, so we should have one less
        assert len(_sessions) == current_sessions - 1, str(_sessions)
    finally:
        manager.load_profile(profile_name)


def test_backup(tmp_path):
    """Test that the backup function creates all the necessary files and folders"""
    storage_backend = get_manager().get_profile_storage()

    # note: this assumes that rsync and pg_dump are in PATH
    storage_backend.backup(str(tmp_path))

    last_backup = tmp_path / 'last-backup'
    assert last_backup.is_symlink()

    # make sure the necessary files are there
    # note: disk-objectstore container backup is already tested in its own repo
    contents = [c.name for c in last_backup.iterdir()]
    for name in ['container', 'db.psql']:
        assert name in contents
