# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aiida.common.exceptions import InvalidOperation
from aiida.common.setup import (get_default_profile, DEFAULT_PROCESS,
                                get_profile_config)
from aiida.backends.sqlalchemy import _GlobalSession
from aiida.backends.sqlalchemy import settings

def is_dbenv_loaded():
    """
    Return if the environment has already been loaded or not.
    """
    pass

def load_dbenv(process=None, profile=None):
    """
    Load the SQLAlchemy database.
    """

    # TODO SP: factorize this at some point ?
    if settings.LOAD_DBENV_CALLED:
        raise InvalidOperation("You cannot call load_dbenv multiple times!")
    settings.LOAD_DBENV_CALLED = True

    if settings.CURRENT_AIIDADB_PROCESS is None and process is None:
        settings.CURRENT_AIIDADB_PROCESS = DEFAULT_PROCESS

    elif (process is not None and process != settings.CURRENT_AIIDADB_PROCESS):
        settings.CURRENT_AIIDADB_PROCESS = process
        settings.AIIDADB_PROFILE = None

    if settings.AIIDADB_PROFILE is not None:
        if profile is not None:
            raise ValueError("You are specifying a profile, but the "
                "settings.AIIDADB_PROFILE is already set")
    else:
        settings.AIIDADB_PROFILE = (profile or
                                    get_default_profile(settings.CURRENT_AIIDADB_PROCESS))

    config = get_profile_config(settings.AIIDADB_PROFILE)

    if config["AIIDADB_ENGINE"] != "postgresql_psycopg2":
        raise ValueError("You can only use SQLAlchemy with the Postgresql backend.")

    engine_url = ("postgresql://{AIIDADB_USER}:{AIIDADB_PASS}@"
                  "{AIIDADB_HOST}:{AIIDADB_PORT}/{AIIDADB_NAME}").format(**config)
    engine = create_engine(engine_url)

    Session = sessionmaker(bind=engine)
    setattr(_GlobalSession, "session", Session())

