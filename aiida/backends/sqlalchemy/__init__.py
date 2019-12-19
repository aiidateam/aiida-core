# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module,global-statement
"""Module with implementation of the database backend using SqlAlchemy."""
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
    """Return a scoped session

    According to SQLAlchemy docs, this returns always the same object within a thread, and a different object in a
    different thread. Moreover, since we update the session class upon forking, different session objects will be used.
    """
    from multiprocessing.util import register_after_fork
    from aiida.manage.configuration import get_profile

    global ENGINE
    global SESSION_FACTORY

    if SESSION_FACTORY is not None:
        session = SESSION_FACTORY()
        return session

    if ENGINE is None:
        ENGINE = create_sqlalchemy_engine(get_profile())

    SESSION_FACTORY = create_scoped_session_factory(ENGINE, expire_on_commit=True)
    register_after_fork(ENGINE, recreate_after_fork)

    return SESSION_FACTORY()


def recreate_after_fork(engine):
    """Callback called after a fork.

    Not only disposes the engine, but also recreates a new scoped session to use independent sessions in the fork.

    :param engine: the engine that will be used by the sessionmaker
    """
    from aiida.manage.configuration import get_profile

    global ENGINE
    global SESSION_FACTORY

    engine.dispose()
    ENGINE = create_sqlalchemy_engine(get_profile())
    SESSION_FACTORY = create_scoped_session_factory(ENGINE, expire_on_commit=True)
