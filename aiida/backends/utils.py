# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.backends import BACKEND_SQLA, BACKEND_DJANGO
from aiida.manage import configuration

AIIDA_ATTRIBUTE_SEP = '.'


def create_sqlalchemy_engine(profile):
    from sqlalchemy import create_engine
    from aiida.common import json

    separator = ':' if profile.database_port else ''
    engine_url = 'postgresql://{user}:{password}@{hostname}{separator}{port}/{name}'.format(
        separator=separator,
        user=profile.database_username,
        password=profile.database_password,
        hostname=profile.database_hostname,
        port=profile.database_port,
        name=profile.database_name
    )
    return create_engine(engine_url, json_serializer=json.dumps, json_deserializer=json.loads, encoding='utf-8')


def create_scoped_session_factory(engine, **kwargs):
    from sqlalchemy.orm import scoped_session, sessionmaker
    return scoped_session(sessionmaker(bind=engine, **kwargs))


def delete_nodes_and_connections(pks):
    if configuration.PROFILE.database_backend == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import delete_nodes_and_connections_django as delete_nodes_backend
    elif configuration.PROFILE.database_backend == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.utils import delete_nodes_and_connections_sqla as delete_nodes_backend
    else:
        raise Exception('unknown backend {}'.format(configuration.PROFILE.database_backend))

    delete_nodes_backend(pks)
