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
import os


def create_mock_profile(name, repository_dirpath=None, **kwargs):
    """Create mock profile for testing purposes.

    :param name: name of the profile
    :param repository_dirpath: optional absolute path to use as the base for the repository path
    """
    from aiida.manage.configuration import Profile, get_config
    from aiida.manage.external.postgres import DEFAULT_DBINFO

    if repository_dirpath is None:
        config = get_config()
        repository_dirpath = config.dirpath

    profile_dictionary = {
        'default_user_email': kwargs.pop('default_user_email', 'dummy@localhost'),
        'storage': {
            'backend': kwargs.pop('storage_backend', 'psql_dos'),
            'config': {
                'database_engine': kwargs.pop('database_engine', 'postgresql_psycopg2'),
                'database_hostname': kwargs.pop('database_hostname', DEFAULT_DBINFO['host']),
                'database_port': kwargs.pop('database_port', DEFAULT_DBINFO['port']),
                'database_name': kwargs.pop('database_name', name),
                'database_username': kwargs.pop('database_username', 'user'),
                'database_password': kwargs.pop('database_password', 'pass'),
                'repository_uri': f"file:///{os.path.join(repository_dirpath, f'repository_{name}')}",
            }
        },
        'process_control': {
            'backend': kwargs.pop('process_control_backend', 'rabbitmq'),
            'config': {
                'broker_protocol': kwargs.pop('broker_protocol', 'amqp'),
                'broker_username': kwargs.pop('broker_username', 'guest'),
                'broker_password': kwargs.pop('broker_password', 'guest'),
                'broker_host': kwargs.pop('broker_host', 'localhost'),
                'broker_port': kwargs.pop('broker_port', 5672),
                'broker_virtual_host': kwargs.pop('broker_virtual_host', ''),
            }
        }
    }

    return Profile(name, profile_dictionary)
