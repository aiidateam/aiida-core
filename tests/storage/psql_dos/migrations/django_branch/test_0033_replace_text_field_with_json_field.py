# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test migration adding the `repository_metadata` column to the `Node` model."""
import json

from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_text_to_jsonb(perform_migrations: PsqlDosMigrator):  # pylint: disable=too-many-locals
    """Test replacing the use of text fields to store JSON data with JSONB fields.

    `db_dbauthinfo.auth_params`, `db_dbauthinfo.metadata`,
    `db_dbauthinfo.transport_params`, `db_dbcomputer.metadata`,
    `db_dblog.metadata`
    """
    # starting revision
    perform_migrations.migrate_up('django@django_0032')

    # setup the database
    user_model = perform_migrations.get_current_table('db_dbuser')
    node_model = perform_migrations.get_current_table('db_dbnode')
    computer_model = perform_migrations.get_current_table('db_dbcomputer')
    authinfo_model = perform_migrations.get_current_table('db_dbauthinfo')
    log_model = perform_migrations.get_current_table('db_dblog')
    with perform_migrations.session() as session:
        user = user_model(
            email='user@aiida.net',
            first_name='John',
            last_name='Doe',
            institution='EPFL',
            password='',
            is_superuser=False,
            is_staff=False,
            is_active=True,
            last_login=timezone.now(),
            date_joined=timezone.now(),
        )
        session.add(user)
        session.commit()
        node = node_model(
            uuid=get_new_uuid(),
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            label='test',
            description='',
            nodeversion=1,
            public=True,
            node_type='node.process.calculation.CalculationNode.',
        )
        session.add(node)
        session.commit()

        computer_metadata = {
            'shebang': '#!/bin/bash',
            'workdir': '/scratch/',
            'append_text': '',
            'prepend_text': '',
            'mpirun_command': ['mpirun', '-np', '{tot_num_mpiprocs}'],
            'default_mpiprocs_per_machine': 1
        }
        computer_transport_params = {'a': 1}
        computer_kwargs = {
            'uuid': get_new_uuid(),
            'name': 'localhost_testing',
            'description': '',
            'hostname': 'localhost',
            'transport_type': 'core.local',
            'scheduler_type': 'core.direct',
            'metadata': json.dumps(computer_metadata),
            'transport_params': json.dumps(computer_transport_params),
        }
        computer = computer_model(**computer_kwargs)
        session.add(computer)
        session.commit()
        computer_id = computer.id

        auth_info_auth_params = {'safe_interval': 2}
        auth_info_metadata = {'safe_interval': 2}
        auth_info_kwargs = {
            'aiidauser_id': user.id,
            'dbcomputer_id': computer.id,
            'enabled': True,
            'auth_params': json.dumps(auth_info_auth_params),
            'metadata': json.dumps(auth_info_metadata),
        }
        authinfo = authinfo_model(**auth_info_kwargs)
        session.add(authinfo)
        session.commit()
        authinfo_id = authinfo.id

        log_metadata = {
            'msecs': 719.0849781036377,
            'lineno': 350,
            'thread': 140011612940032,
            'asctime': '10/21/2018 12:39:51 PM',
            'created': 1540118391.719085,
            'levelno': 23,
            'message': 'calculation node 1',
        }
        log_kwargs = {
            'uuid': get_new_uuid(),
            'time': timezone.now(),
            'loggername': 'localhost',
            'levelname': 'localhost',
            'message': '',
            'dbnode_id': node.id,
            'metadata': json.dumps(log_metadata)
        }
        log = log_model(**log_kwargs)
        session.add(log)
        session.commit()
        log_id = log.id

    # final revision
    perform_migrations.migrate_up('django@django_0033')

    computer_model = perform_migrations.get_current_table('db_dbcomputer')
    authinfo_model = perform_migrations.get_current_table('db_dbauthinfo')
    log_model = perform_migrations.get_current_table('db_dblog')
    with perform_migrations.session() as session:

        computer = session.query(computer_model).filter(computer_model.id == computer_id).one()
        assert computer.metadata == computer_metadata
        assert computer.transport_params == computer_transport_params

        authinfo = session.query(authinfo_model).filter(authinfo_model.id == authinfo_id).one()
        assert authinfo.auth_params == auth_info_auth_params
        assert authinfo.metadata == auth_info_metadata

        log = session.query(log_model).filter(log_model.id == log_id).one()
        assert log.metadata == log_metadata
