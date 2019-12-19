# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=global-statement
"""Module with implementation of the database backend using Django."""
from aiida.backends.utils import create_sqlalchemy_engine, create_scoped_session_factory

ENGINE = None
SESSION_FACTORY = None


def reset_session():
    """Reset the session which means setting the global engine and session factory instances to `None`."""
    global ENGINE
    global SESSION_FACTORY

    if ENGINE is not None:
        ENGINE.dispose()

    if SESSION_FACTORY is not None:
        SESSION_FACTORY.expunge_all()  # pylint: disable=no-member
        SESSION_FACTORY.close()  # pylint: disable=no-member

    ENGINE = None
    SESSION_FACTORY = None


def get_scoped_session():
    """Return a scoped session for the given profile that is exclusively to be used for the `QueryBuilder`.

    Since the `QueryBuilder` implementation uses SqlAlchemy to map the query onto the models in order to generate the
    SQL to be sent to the database, it requires a session, which is an :class:`sqlalchemy.orm.session.Session` instance.
    The only purpose is for SqlAlchemy to be able to connect to the database perform the query and retrieve the results.
    Even the Django backend implementation will use SqlAlchemy for its `QueryBuilder` and so also needs an SqlA session.
    It is important that we do not reuse the scoped session factory in the SqlAlchemy implementation, because that runs
    the risk of cross-talk once profiles can be switched dynamically in a single python interpreter. Therefore the
    Django implementation of the `QueryBuilder` should keep its own SqlAlchemy engine and scoped session factory
    instances that are used to provide the query builder with a session.

    :param profile: :class:`aiida.manage.configuration.profile.Profile` for which to configure the engine.
    :return: :class:`sqlalchemy.orm.session.Session` instance with engine configured for the given profile.
    """
    from aiida.manage.configuration import get_profile

    global ENGINE
    global SESSION_FACTORY

    if SESSION_FACTORY is not None:
        session = SESSION_FACTORY()
        return session

    if ENGINE is None:
        ENGINE = create_sqlalchemy_engine(get_profile())

    SESSION_FACTORY = create_scoped_session_factory(ENGINE)

    return SESSION_FACTORY()
