# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Tests for the :mod:`aiida.cmdline.utils.decorators` module."""
import pytest

from aiida.cmdline.utils.decorators import load_backend_if_not_loaded
from aiida.common.exceptions import InvalidOperation
from aiida.manage import get_manager


@pytest.fixture
def config(empty_config, profile_factory):
    """Return an isolated configuration with two profiles configured and the first set as the default."""
    config = empty_config
    profile_one = profile_factory(name='profile-one')
    profile_two = profile_factory(name='profile-two')
    config.add_profile(profile_one)
    config.add_profile(profile_two)
    config.set_default_profile(profile_one.name)
    yield config


@pytest.fixture
def manager(monkeypatch):
    """Return a ``Manager`` instance with the ``get_profile_storage`` method mocked."""
    manager = get_manager()

    class StorageBackend:
        """Mock version of :class:`aiida.orm.implementation.storage_backend.StorageBackend`."""

        def close(self):
            pass

    def get_profile_storage(self):
        """Set a mock version of the storage backend."""
        self._profile_storage = StorageBackend()  # pylint: disable=protected-access

    monkeypatch.setattr(manager.__class__, 'get_profile_storage', get_profile_storage)
    yield manager


def test_load_backend_if_not_loaded(config, manager):
    """Test the :meth:`aiida.cmdline.utils.decorators.load_backend_if_not_loaded` if no profile is loaded."""
    assert manager.get_profile() is None

    load_backend_if_not_loaded()
    assert manager.get_profile().name == config.default_profile_name

    with pytest.raises(InvalidOperation, match=r'cannot switch to profile .* allow_switch is False'):
        manager.load_profile('profile-two')


def test_load_backend_if_not_loaded_with_loaded_profile(config, manager):
    """Test the :meth:`aiida.cmdline.utils.decorators.load_backend_if_not_loaded` if a profile is already loaded."""
    manager.load_profile('profile-two')
    assert manager.get_profile().name == 'profile-two'
    assert config.default_profile_name != 'profile-two'

    # Calling the method again should keep the currently loaded profile, and not switch to the default profile
    load_backend_if_not_loaded()
    assert manager.get_profile().name == 'profile-two'
