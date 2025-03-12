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
from aiida.orm import authinfos, computers
from aiida.orm.implementation.authinfos import BackendAuthInfo


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

        try:
            auth_params['password'] = 'pw'
            self.auth_info.set_auth_params(auth_params)
            assert self.auth_info.get_auth_params()['password'] == authinfos.Password.OBFUSCATED
            assert self.auth_info.secure_storage.get_password() == 'pw'
        finally:
            self.auth_info.secure_storage.delete_password()

    def test_secure_storage(self):
        # Check get_password
        assert self.auth_info.secure_storage.get_password() is None
        try:
            # Check set_password
            self.auth_info.secure_storage.set_password('password')
            assert self.auth_info.secure_storage.get_password() == 'password'

            # Check set_password get_password_cmd_stdout_password

            cmd_stdout_password = self.auth_info.secure_storage.get_cmd_stdout_password()
            result = subprocess.run(shlex.split(cmd_stdout_password), capture_output=True, text=True, check=False)
            assert result.stdout == 'password'
        finally:
            self.auth_info.secure_storage.delete_password()

        # Check delete_password
        assert self.auth_info.secure_storage.get_password() is None

    def test_delete_authinfo(self):
        """Test deleting a single AuthInfo."""
        pk = self.auth_info.pk
        # Check setting password works properly
        self.auth_info.secure_storage.set_password('pw')
        assert self.auth_info.secure_storage.get_password() == 'pw'

        assert len(authinfos.AuthInfo.collection.all()) == 1
        authinfos.AuthInfo.collection.delete(pk)
        assert len(authinfos.AuthInfo.collection.all()) == 0

        with pytest.raises(exceptions.NotExistent):
            authinfos.AuthInfo.collection.delete(pk)

        # Check password has been also deleted
        # We have to create a new SecureStorage as auth_info is now invalid
        assert BackendAuthInfo.SecureStorage(self.computer).get_password() is None

    def test_delete_computer(self):
        """Test that deleting a computer also deletes the associated Authinfo."""
        pk = self.auth_info.pk

        # Check setting password works properly
        self.auth_info.secure_storage.set_password('pw')
        assert self.auth_info.secure_storage.get_password() == 'pw'

        computers.Computer.collection.delete(self.computer.pk)
        with pytest.raises(exceptions.NotExistent):
            authinfos.AuthInfo.collection.delete(pk)

        # Check password has been also deleted
        # We have to create a new SecureStorage as auth_info is now invalid
        assert BackendAuthInfo.SecureStorage(self.computer).get_password() is None
