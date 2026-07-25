###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the AuthInfo ORM class."""

import shlex
import subprocess

import pytest

from aiida.common import exceptions
from aiida.common.datastructures import SecureStorage
from aiida.orm import authinfos, computers, users


class MockEntry:
    """Mock keyring entry for testing secure-storage cleanup."""

    def __init__(self, exception: Exception | None) -> None:
        self.exception = exception

    def set_password(self, password: str):
        """Accept storing the password."""

    def delete_credential(self):
        """Raise the configured exception."""
        if self.exception is not None:
            raise self.exception


def test_init_auth_params_stores_password_in_secure_storage(aiida_profile_clean, aiida_localhost, monkeypatch):
    """Passing auth params to the constructor should not persist plaintext passwords."""
    monkeypatch.setattr(SecureStorage, '_entry', lambda _: MockEntry(None))
    user = users.User(email='constructor@localhost').store()

    auth_info = authinfos.AuthInfo(computer=aiida_localhost, user=user, auth_params={'password': 'pw'}).store()

    assert SecureStorage.contains_redacted_password(auth_info.get_auth_params())
    assert auth_info.get_auth_params()['password'] != 'pw'


@pytest.mark.parametrize('entity', ('authinfo', 'computer'))
@pytest.mark.parametrize('has_password', (False, True))
def test_delete_cleans_secure_storage_best_effort(
    aiida_profile_clean, aiida_localhost, monkeypatch, entity, has_password
):
    """Deleting an authinfo or computer only cleans up secure storage if a password was stored."""
    auth_info = aiida_localhost.configure()
    if has_password:
        monkeypatch.setattr(SecureStorage, '_entry', lambda _: MockEntry(None))
        auth_info.set_auth_params({'password': 'pw'})

    exception = (
        OSError('No secure-storage backend available.')
        if has_password
        else AssertionError('Secure-storage cleanup should not have been attempted.')
    )
    monkeypatch.setattr(SecureStorage, '_entry', lambda _: MockEntry(exception))

    if entity == 'authinfo':
        authinfos.AuthInfo.collection.delete(auth_info.pk)
        assert len(authinfos.AuthInfo.collection.all()) == 0
    else:
        computers.Computer.collection.delete(aiida_localhost.pk)
        assert len(computers.Computer.collection.all()) == 0


def test_delete_authinfo_removes_only_its_own_secure_password(aiida_profile_clean, aiida_localhost, monkeypatch):
    """Each authinfo owns a separate credential (keyed per computer and user); deleting one must not remove another's.

    A computer can have multiple authinfos, one per user. Since each stores its password under its own keyring
    entry, deleting one authinfo cleans up only that entry, leaving other users' passwords intact.
    """
    store: dict[str, str] = {}

    class DictEntry:
        """Mock keyring entry backed by ``store``, keyed by the secure-storage entry name."""

        def __init__(self, secure_storage: SecureStorage) -> None:
            self._name = secure_storage._entry_name

        def set_password(self, password: str) -> None:
            store[self._name] = password

        def get_password(self) -> str:
            if self._name not in store:
                raise KeyError(self._name)
            return store[self._name]

        def delete_credential(self) -> None:
            if self._name not in store:
                raise KeyError(self._name)
            del store[self._name]

    def get_dict_entry(secure_storage: SecureStorage) -> DictEntry:
        return DictEntry(secure_storage)

    monkeypatch.setattr(SecureStorage, '_entry', get_dict_entry)

    default_auth_info = aiida_localhost.configure()
    default_auth_info.set_auth_params({'password': 'pw-default'})
    other_user = users.User(email='other@localhost').store()
    other_auth_info = authinfos.AuthInfo(
        computer=aiida_localhost, user=other_user, auth_params={'password': 'pw-other'}
    ).store()

    # The two authinfos store their passwords under distinct entries.
    assert len(store) == 2

    # Deleting one authinfo removes only its own credential; the other user's password is untouched.
    authinfos.AuthInfo.collection.delete(other_auth_info.pk)
    assert list(store.values()) == ['pw-default']


class TestAuthinfo:
    """Unit tests for the AuthInfo ORM class."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_profile_clean, aiida_localhost):
        """Initialize the profile."""
        self.computer = aiida_localhost
        self.auth_info = self.computer.configure()

    def test_set_auth_params(self):
        """Test the auth_params setter."""
        auth_params = {'safe_interval': 100}

        self.auth_info.set_auth_params(auth_params)
        assert self.auth_info.get_auth_params() == auth_params

        secure_storage = SecureStorage(self.computer.uuid, self.auth_info.user.pk)
        try:
            auth_params['password'] = 'pw'
            self.auth_info.set_auth_params(auth_params)
            assert SecureStorage.contains_redacted_password(self.auth_info.get_auth_params())
            assert secure_storage.get_password() == 'pw'

            # Round-tripping the auth params must not alter the password in secure storage
            self.auth_info.set_auth_params(self.auth_info.get_auth_params())
            assert SecureStorage.contains_redacted_password(self.auth_info.get_auth_params())
            assert secure_storage.get_password() == 'pw'
        finally:
            secure_storage.delete_password()

    def test_secure_storage(self):
        secure_storage = SecureStorage(self.computer.uuid, self.auth_info.user.pk)
        # Check get_password
        assert secure_storage.get_password() is None
        try:
            # Check set_password
            secure_storage.set_password('password')
            assert secure_storage.get_password() == 'password'

            # The generated command must print the stored password to stdout
            cmd_stdout_password = secure_storage.get_cmd_stdout_password()
            result = subprocess.run(shlex.split(cmd_stdout_password), capture_output=True, text=True, check=False)
            assert result.stdout == 'password'
        finally:
            secure_storage.delete_password()

        # Check delete_password
        assert secure_storage.get_password() is None

    def test_delete_authinfo(self):
        """Test deleting a single AuthInfo."""
        pk = self.auth_info.pk
        user_pk = self.auth_info.user.pk
        # Storing a password marks the authinfo and persists the credential in secure storage.
        self.auth_info.set_auth_params({'password': 'pw'})
        assert SecureStorage(self.computer.uuid, user_pk).get_password() == 'pw'

        assert len(authinfos.AuthInfo.collection.all()) == 1
        authinfos.AuthInfo.collection.delete(pk)
        assert len(authinfos.AuthInfo.collection.all()) == 0

        with pytest.raises(exceptions.NotExistent):
            authinfos.AuthInfo.collection.delete(pk)

        # Check password has been also deleted
        # We have to create a new SecureStorage as auth_info is now invalid
        assert SecureStorage(self.computer.uuid, user_pk).get_password() is None

    def test_delete_authinfo_keeps_other_users_password(self):
        """Deleting one authinfo must keep another user's password, as each authinfo owns a separate credential."""
        other_user = users.User(email='other@localhost').store()
        other_auth_info = authinfos.AuthInfo(computer=self.computer, user=other_user).store()

        secure_storage = SecureStorage(self.computer.uuid, self.auth_info.user.pk)
        try:
            self.auth_info.set_auth_params({'password': 'pw'})
            other_auth_info.set_auth_params({'password': 'pw'})
            authinfos.AuthInfo.collection.delete(other_auth_info.pk)
            assert secure_storage.get_password() == 'pw'
        finally:
            secure_storage.delete_password()

    def test_delete_computer(self):
        """Test that deleting a computer also deletes the associated Authinfo."""
        pk = self.auth_info.pk
        user_pk = self.auth_info.user.pk

        # Storing a password marks the authinfo and persists the credential in secure storage.
        self.auth_info.set_auth_params({'password': 'pw'})
        assert SecureStorage(self.computer.uuid, user_pk).get_password() == 'pw'

        computers.Computer.collection.delete(self.computer.pk)
        with pytest.raises(exceptions.NotExistent):
            authinfos.AuthInfo.collection.delete(pk)

        # Check password has been also deleted
        # We have to create a new SecureStorage as auth_info is now invalid
        assert SecureStorage(self.computer.uuid, user_pk).get_password() is None
