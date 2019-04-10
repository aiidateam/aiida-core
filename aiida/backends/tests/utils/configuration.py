# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module that defines methods to mock an AiiDA instance complete with mock configuration and profile."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import contextlib
import os
import shutil
import tempfile


def create_mock_profile(name, repository_dirpath=None):
    """Create mock profile for testing purposes.

    :param name: name of the profile
    :param repository_dirpath: optional absolute path to use as the base for the repository path
    """
    from aiida.manage.configuration import get_config, Profile

    if repository_dirpath is None:
        config = get_config()
        repository_dirpath = config.dirpath

    profile_dictionary = {
        'default_user': 'dummy@localhost',
        'database_engine': 'postgresql_psycopg2',
        'database_backend': 'django',
        'database_name': name,
        'database_port': '5432',
        'database_hostname': 'localhost',
        'database_username': 'user',
        'database_password': 'pass',
        'repository_uri': 'file:///' + os.path.join(repository_dirpath, 'repository_' + name),
    }

    return Profile(name, profile_dictionary)


@contextlib.contextmanager
def temporary_config_instance():
    """Create a temporary AiiDA instance."""
    current_config = None
    current_config_path = None
    current_profile = None
    temporary_config_directory = None

    from aiida.manage import configuration
    from aiida.manage.configuration import settings

    try:
        from aiida.manage.configuration.settings import create_instance_directories

        # Store the current configuration instance and config directory path
        current_config = configuration.CONFIG
        current_config_path = current_config.dirpath
        current_profile = configuration.PROFILE

        # Create a temporary folder, set it as the current config directory path and reset the loaded configuration
        profile_name = 'test_profile_1234'
        temporary_config_directory = tempfile.mkdtemp()
        configuration.CONFIG = None
        settings.AIIDA_CONFIG_FOLDER = temporary_config_directory

        # Create the instance base directory structure, the config file and a dummy profile
        create_instance_directories()
        configuration.CONFIG = configuration.load_config(create=True)
        profile = create_mock_profile(name=profile_name, repository_dirpath=temporary_config_directory)
        configuration.PROFILE = profile

        # Add the created profile and set it as the default
        configuration.CONFIG.add_profile(profile)
        configuration.CONFIG.set_default_profile(profile_name, overwrite=True)
        configuration.CONFIG.store()

        yield configuration.CONFIG
    finally:
        # Reset the config folder path and the config instance
        configuration.CONFIG = current_config
        settings.AIIDA_CONFIG_FOLDER = current_config_path
        configuration.PROFILE = current_profile

        # Destroy the temporary instance directory
        if temporary_config_directory and os.path.isdir(temporary_config_directory):
            shutil.rmtree(temporary_config_directory)


def with_temporary_config_instance(function):
    """Create a temporary AiiDA instance for the duration of the wrapped function."""

    def decorated_function(*args, **kwargs):
        with temporary_config_instance():
            function(*args, **kwargs)

    return decorated_function


@contextlib.contextmanager
def temporary_directory():
    """Create a temporary directory."""
    try:
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def with_temp_dir(function):
    """Create a temporary directory for the duration of the wrapped function.

    The path of the temporary directory is passed to the wrapped function via
    the 'temp_dir' parameter (which it must accept).
    """

    def decorated_function(*args, **kwargs):
        with temporary_directory() as tmpdir:
            function(*args, temp_dir=tmpdir, **kwargs)

    return decorated_function
