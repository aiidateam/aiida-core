# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aiida.common.exceptions import InvalidOperation, ConfigurationError
from aiida.common.setup import (get_default_profile, DEFAULT_PROCESS,
                                get_profile_config, DEFAULT_USER_CONFIG_FIELD)
from aiida.backends import sqlalchemy
from aiida.backends.sqlalchemy import settings

# Those import are necessary for SQLAlchemy to correvtly detect the models
from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
from aiida.backends.sqlalchemy.models.calcstate import DbCalcState
from aiida.backends.sqlalchemy.models.comment import DbComment
from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.backends.sqlalchemy.models.group import DbGroup
from aiida.backends.sqlalchemy.models.lock import DbLock
from aiida.backends.sqlalchemy.models.log import DbLog
from aiida.backends.sqlalchemy.models.node import DbLink, DbNode, DbPath
from aiida.backends.sqlalchemy.models.user import DbUser
from aiida.backends.sqlalchemy.models.workflow import DbWorkflow, DbWorkflowData, DbWorkflowStep


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
    sqlalchemy.session = Session()


def get_automatic_user():
    global _aiida_autouser_cache

    if _aiida_autouser_cache is not None:
        return _aiida_autouser_cache

    email = get_configured_user_email()

    _aiida_autouser_cache = DbUser.query.filter(DbUser.email == email).first()

    if not _aiida_autouser_cache:
        raise ConfigurationError("No aiida user with email {}".format(
            email))
    return _aiida_autouser_cache

def get_configured_user_email():
    """
    Return the email (that is used as the username) configured during the
    first verdi install.
    """
    try:
        profile_conf = get_profile_config(settings.AIIDADB_PROFILE,
                                          set_test_location=False)
        email = profile_conf[DEFAULT_USER_CONFIG_FIELD]
    # I do not catch the error in case of missing configuration, because
    # it is already a ConfigurationError
    except KeyError:
        raise ConfigurationError("No 'default_user' key found in the "
                                 "AiiDA configuration file")
    return email
