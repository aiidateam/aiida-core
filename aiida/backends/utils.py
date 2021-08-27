# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend-agnostic utility functions"""
from aiida.backends import BACKEND_SQLA, BACKEND_DJANGO
from aiida.manage import configuration

AIIDA_ATTRIBUTE_SEP = '.'


def create_sqlalchemy_engine(profile, **kwargs):
    """Create SQLAlchemy engine (to be used for QueryBuilder queries)

    :param kwargs: keyword arguments that will be passed on to `sqlalchemy.create_engine`.
        See https://docs.sqlalchemy.org/en/13/core/engines.html?highlight=create_engine#sqlalchemy.create_engine for
        more info.
    """
    from sqlalchemy import create_engine
    from aiida.common import json

    # The hostname may be `None`, which is a valid value in the case of peer authentication for example. In this case
    # it should be converted to an empty string, because otherwise the `None` will be converted to string literal "None"
    hostname = profile.database_hostname or ''
    separator = ':' if profile.database_port else ''

    engine_url = 'postgresql://{user}:{password}@{hostname}{separator}{port}/{name}'.format(
        separator=separator,
        user=profile.database_username,
        password=profile.database_password,
        hostname=hostname,
        port=profile.database_port,
        name=profile.database_name
    )
    return create_engine(
        engine_url, json_serializer=json.dumps, json_deserializer=json.loads, future=False, encoding='utf-8', **kwargs
    )


def create_scoped_session_factory(engine, **kwargs):
    """Create scoped SQLAlchemy session factory"""
    from sqlalchemy.orm import scoped_session, sessionmaker
    return scoped_session(sessionmaker(bind=engine, **kwargs))


def delete_nodes_and_connections(pks):
    """Backend-agnostic function to delete Nodes and connections"""
    if configuration.PROFILE.database_backend == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import delete_nodes_and_connections_django as delete_nodes_backend
    elif configuration.PROFILE.database_backend == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.utils import delete_nodes_and_connections_sqla as delete_nodes_backend
    else:
        raise Exception(f'unknown backend {configuration.PROFILE.database_backend}')

    delete_nodes_backend(pks)
