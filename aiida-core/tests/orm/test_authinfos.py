###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the AuthInfo ORM class."""

import pytest

from aiida.common import exceptions
from aiida.orm import authinfos, computers


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

    def test_delete_authinfo(self):
        """Test deleting a single AuthInfo."""
        pk = self.auth_info.pk

        assert len(authinfos.AuthInfo.collection.all()) == 1
        authinfos.AuthInfo.collection.delete(pk)
        assert len(authinfos.AuthInfo.collection.all()) == 0

        with pytest.raises(exceptions.NotExistent):
            authinfos.AuthInfo.collection.delete(pk)

    def test_delete_computer(self):
        """Test that deleting a computer also deletes the associated Authinfo."""
        pk = self.auth_info.pk

        computers.Computer.collection.delete(self.computer.pk)
        with pytest.raises(exceptions.NotExistent):
            authinfos.AuthInfo.collection.delete(pk)
