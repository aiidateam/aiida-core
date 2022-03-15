# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-self-use
"""Tests for the Profile class."""
import os
import uuid

import pytest

from aiida.manage.configuration import Profile
from tests.utils.configuration import create_mock_profile


class TestProfile:
    """Tests for the Profile class."""

    @pytest.fixture(autouse=True)
    def init_profile(self):  # pylint: disable=unused-argument
        """Initialize the profile."""
        # pylint: disable=attribute-defined-outside-init
        self.profile_name = 'test_profile'
        self.profile_dictionary = {
            'test_profile': True,
            'default_user_email': 'dummy@localhost',
            'storage': {
                'backend': 'psql_dos',
                'config': {
                    'database_engine': 'postgresql_psycopg2',
                    'database_name': self.profile_name,
                    'database_port': '5432',
                    'database_hostname': 'localhost',
                    'database_username': 'user',
                    'database_password': 'pass',
                    'repository_uri': f"file:///{os.path.join('/some/path', f'repository_{self.profile_name}')}",
                }
            },
            'process_control': {
                'backend': 'rabbitmq',
                'config': {
                    'broker_protocol': 'amqp',
                    'broker_username': 'guest',
                    'broker_password': 'guest',
                    'broker_host': 'localhost',
                    'broker_port': 5672,
                    'broker_virtual_host': '',
                }
            }
        }
        self.profile = Profile(self.profile_name, self.profile_dictionary)

    def test_base_properties(self):
        """Test the basic properties of a Profile instance."""
        assert self.profile.name == self.profile_name

        assert self.profile.storage_backend == 'psql_dos'
        assert self.profile.storage_config == self.profile_dictionary['storage']['config']
        assert self.profile.process_control_backend == 'rabbitmq'
        assert self.profile.process_control_config == self.profile_dictionary['process_control']['config']

        # Verify that the uuid property returns a valid UUID by attempting to construct an UUID instance from it
        uuid.UUID(self.profile.uuid)

        # Check that the default user email field is not None
        assert self.profile.default_user_email is not None

        # The RabbitMQ prefix should contain the profile UUID
        assert self.profile.uuid in self.profile.rmq_prefix

    def test_is_test_profile(self):
        """Test the :meth:`aiida.manage.configuration.profile.is_test_profile` property."""
        profile = create_mock_profile(name='not_test_profile')
        profile.is_test_profile = False

        # The one constructed in the setUpClass should be a test profile
        assert self.profile.is_test_profile

        # The profile created here should *not* be a test profile
        assert not profile.is_test_profile

    def test_set_option(self):
        """Test the `set_option` method."""
        option_key = 'daemon.timeout'
        option_value_one = 999
        option_value_two = 666

        # Setting an option if it does not exist should work
        self.profile.set_option(option_key, option_value_one)
        assert self.profile.get_option(option_key) == option_value_one

        # Setting it again will override it by default
        self.profile.set_option(option_key, option_value_two)
        assert self.profile.get_option(option_key) == option_value_two

        # If we set override to False, it should not override, big surprise
        self.profile.set_option(option_key, option_value_one, override=False)
        assert self.profile.get_option(option_key) == option_value_two
