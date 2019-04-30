# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

# The next two serve as global variables, set in the `load_dbenv` call and should be properly reset upon forking.
ENGINE = None
SCOPED_SESSION_CLASS = None


def get_scoped_session():
    """Return a scoped session

    According to SQLAlchemy docs, this returns always the same object within a thread, and a different object in a
    different thread. Moreover, since we update the session class upon forking, different session objects will be used.
    """
    global SCOPED_SESSION_CLASS

    if SCOPED_SESSION_CLASS is None:
        reset_session()

    return SCOPED_SESSION_CLASS()


def recreate_after_fork(engine):
    """Callback called after a fork.

    Not only disposes the engine, but also recreates a new scoped session to use independent sessions in the fork.

    :param engine: the engine that will be used by the sessionmaker
    """
    global ENGINE
    global SCOPED_SESSION_CLASS

    ENGINE.dispose()
    SCOPED_SESSION_CLASS = scoped_session(sessionmaker(bind=ENGINE, expire_on_commit=True))


def reset_session(profile=None):
    """
    Resets (global) engine and sessionmaker classes, to create a new one
    (or creates a new one from scratch if not already available)

    :param profile: the profile whose configuration to use to connect to the database
    """
    from multiprocessing.util import register_after_fork
    from aiida.manage.configuration import get_profile
    from .utils import loads_json, dumps_json

    global ENGINE
    global SCOPED_SESSION_CLASS

    if profile is None:
        profile = get_profile()

    separator = ':' if profile.database_port else ''
    engine_url = 'postgresql://{user}:{password}@{hostname}{separator}{port}/{name}'.format(
        separator=separator,
        user=profile.database_username,
        password=profile.database_password,
        hostname=profile.database_hostname,
        port=profile.database_port,
        name=profile.database_name)

    ENGINE = create_engine(engine_url, json_serializer=dumps_json, json_deserializer=loads_json, encoding='utf-8')
    SCOPED_SESSION_CLASS = scoped_session(sessionmaker(bind=ENGINE, expire_on_commit=True))
    register_after_fork(ENGINE, recreate_after_fork)
