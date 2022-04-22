# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :class:`aiida.manage.configuration.profile.Profile` class."""
import uuid

import pytest


def test_base_properties(profile_factory):
    """Test the basic properties of a ``Profile`` instance."""
    kwargs = {
        'name': 'profile-name',
        'storage_backend': 'core.psql_dos',
        'process_control_backend': 'rabbitmq',
    }
    profile = profile_factory(**kwargs)

    assert profile.name == kwargs['name']
    assert profile.storage_backend == kwargs['storage_backend']
    assert profile.process_control_backend == kwargs['process_control_backend']

    # Verify that the uuid property returns a valid UUID by attempting to construct an UUID instance from it
    uuid.UUID(profile.uuid)

    # Check that the default user email field is not None
    assert profile.default_user_email is not None

    # The RabbitMQ prefix should contain the profile UUID
    assert profile.uuid in profile.rmq_prefix


@pytest.mark.parametrize('test_profile', (True, False))
def test_is_test_profile(profile_factory, test_profile):
    """Test the :meth:`aiida.manage.configuration.profile.is_test_profile` property."""
    profile = profile_factory(test_profile=test_profile)
    assert profile.is_test_profile is test_profile


def test_set_option(profile_factory):
    """Test the `set_option` method."""
    profile = profile_factory()
    option_key = 'daemon.timeout'
    option_value_one = 999
    option_value_two = 666

    # Setting an option if it does not exist should work
    profile.set_option(option_key, option_value_one)
    assert profile.get_option(option_key) == option_value_one

    # Setting it again will override it by default
    profile.set_option(option_key, option_value_two)
    assert profile.get_option(option_key) == option_value_two

    # If we set override to False, it should not override, big surprise
    profile.set_option(option_key, option_value_one, override=False)
    assert profile.get_option(option_key) == option_value_two
