# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module that defines methods to mock an AiiDA instance complete with mock configuration and profile."""

import contextlib
import os
import shutil
import tempfile


def create_mock_profile(name, repository_dirpath=None, **kwargs):
    """Create mock profile for testing purposes.

    :param name: name of the profile
    :param repository_dirpath: optional absolute path to use as the base for the repository path
    """
    from aiida.manage.configuration import get_config, Profile
    from aiida.manage.external.postgres import DEFAULT_DBINFO

    if repository_dirpath is None:
        config = get_config()
        repository_dirpath = config.dirpath

    profile_dictionary = {
        'default_user': kwargs.pop('default_user', 'dummy@localhost'),
        'database_engine': kwargs.pop('database_engine', 'postgresql_psycopg2'),
        'database_backend': kwargs.pop('database_backend', 'django'),
        'database_hostname': kwargs.pop('database_hostname', DEFAULT_DBINFO['host']),
        'database_port': kwargs.pop('database_port', DEFAULT_DBINFO['port']),
        'database_name': kwargs.pop('database_name', name),
        'database_username': kwargs.pop('database_username', 'user'),
        'database_password': kwargs.pop('database_password', 'pass'),
        'repository_uri': f"file:///{os.path.join(repository_dirpath, f'repository_{name}')}",
    }

    return Profile(name, profile_dictionary)


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
