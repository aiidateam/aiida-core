# -*- coding: utf-8 -*-

from __future__ import absolute_import

from aiida.backends import settings
from aiida.backends.profile import load_profile, BACKEND_SQLA, BACKEND_DJANGO
from aiida.common.exceptions import (
        ConfigurationError, AuthenticationError,
        InvalidOperation
    )


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"


def is_dbenv_loaded():
    """
    Return True of the dbenv was already loaded (with a call to load_dbenv),
    False otherwise.
    """
    return settings.LOAD_DBENV_CALLED


def load_dbenv(process=None, profile=None, *args, **kwargs):
    if is_dbenv_loaded():
        raise InvalidOperation("You cannot call load_dbenv multiple times!")
    settings.LOAD_DBENV_CALLED = True

    # This is going to set global variables in settings, including
    # settings.BACKEND
    load_profile(process=process, profile=profile)

    if settings.BACKEND == BACKEND_SQLA:
        # Maybe schema version should be also checked for SQLAlchemy version.
        from aiida.backends.sqlalchemy.utils \
            import load_dbenv as load_dbenv_sqlalchemy
        return load_dbenv_sqlalchemy(
            process=process, profile=profile, *args, **kwargs)
    elif settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import load_dbenv as load_dbenv_django
        return load_dbenv_django(
            process=process, profile=profile, *args, **kwargs)
    else:
        raise ConfigurationError("Invalid settings.BACKEND: {}".format(
            settings.BACKEND))


def get_automatic_user():
    if settings.BACKEND == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.utils import (
            get_automatic_user as get_automatic_user_sqla)
        return get_automatic_user_sqla()
    elif settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import (
            get_automatic_user as get_automatic_user_dj)
        return get_automatic_user_dj()
    else:
        raise ValueError("This method doesn't exist for this backend")


def get_workflow_list(*args, **kwargs):
    if settings.BACKEND == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.cmdline import (
            get_workflow_list as get_workflow_list_sqla)
        return get_workflow_list_sqla(*args, **kwargs)
    elif settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.cmdline import (
            get_workflow_list as get_workflow_list_dj)
        return get_workflow_list_dj(*args, **kwargs)
    else:
        raise ValueError("This method doesn't exist for this backend")


def get_log_messages(*args, **kwargs):
    if settings.BACKEND == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.cmdline import (
            get_log_messages as get_log_messages_sqla)
        return get_log_messages_sqla(*args, **kwargs)
    elif settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.cmdline import (
            get_log_messages as get_log_messages_dj)
        return get_log_messages_dj(*args, **kwargs)
    else:
        raise ValueError("This method doesn't exist for this backend")


def get_authinfo(computer, aiidauser):

    if settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.db.models import DbComputer, DbAuthInfo
        from django.core.exceptions import (ObjectDoesNotExist,
                                            MultipleObjectsReturned)

        try:
            authinfo = DbAuthInfo.objects.get(
                # converts from name, Computer or DbComputer instance to
                # a DbComputer instance
                dbcomputer=DbComputer.get_dbcomputer(computer),
                aiidauser=aiidauser)
        except ObjectDoesNotExist:
            raise AuthenticationError(
                "The aiida user {} is not configured to use computer {}".format(
                    aiidauser.email, computer.name))
        except MultipleObjectsReturned:
            raise ConfigurationError(
                "The aiida user {} is configured more than once to use "
                "computer {}! Only one configuration is allowed".format(
                    aiidauser.email, computer.name))
    elif settings.BACKEND == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
        from aiida.backends.sqlalchemy import session
        from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
        try:
            authinfo = session.query(DbAuthInfo).filter_by(
                dbcomputer_id=computer.id,
                aiidauser_id=aiidauser.id,
            ).one()
        except NoResultFound:
            raise AuthenticationError(
                "The aiida user {} is not configured to use computer {}".format(
                    aiidauser.email, computer.name))
        except MultipleResultsFound:
            raise ConfigurationError(
                "The aiida user {} is configured more than once to use "
                "computer {}! Only one configuration is allowed".format(
                    aiidauser.email, computer.name))

    else:
        raise Exception("unknown backend {}".format(settings.BACKEND))
    return authinfo


def get_daemon_user():
    if settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import (get_daemon_user
                                                 as get_daemon_user_dj)
        daemon_user = get_daemon_user_dj()
    elif settings.BACKEND == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.utils import (get_daemon_user
                                                     as get_daemon_user_sqla)
        daemon_user = get_daemon_user_sqla()
    return daemon_user


def set_daemon_user(user_email):
    if settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import (set_daemon_user
                                                 as set_daemon_user_dj)
        set_daemon_user_dj(user_email)
    elif settings.BACKEND == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.utils import (set_daemon_user
                                                     as set_daemon_user_sqla)
        set_daemon_user_sqla(user_email)


def get_global_setting(key):
    if settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.globalsettings import get_global_setting
        from django.db import connection
        if 'db_dbsetting' not in connection.introspection.table_names():
            raise KeyError("No table found")
    elif settings.BACKEND == BACKEND_SQLA:
        from sqlalchemy.engine import reflection
        from aiida.backends import sqlalchemy as sa
        inspector = reflection.Inspector.from_engine(sa.session.bind)
        if 'db_dbsetting' not in inspector.get_table_names():
            raise KeyError("No table found")
        from aiida.backends.sqlalchemy.globalsettings import get_global_setting
    else:
        raise Exception("unknown backend {}".format(settings.BACKEND))
    return get_global_setting(key)


def get_db_schema_version():
    """
    Get the current schema version stored in the DB. Return None if
    it is not stored.
    """
    try:
        return get_global_setting('db|schemaversion')
    except KeyError:
        return None


def get_backend_type():
    """
    Set the schema version stored in the DB. Use only if you know what
    you are doing.
    """
    return get_global_setting('db|backend')


def set_global_setting(key, value, description=None):
    if settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.globalsettings import set_global_setting
    elif settings.BACKEND == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.globalsettings import set_global_setting
    else:
        raise Exception("unknown backend {}".format(settings.BACKEND))

    set_global_setting(key, value, description)


def set_db_schema_version(version):
    """
    Set the schema version stored in the DB. Use only if you know what
    you are doing.
    """
    return set_global_setting(
        'db|schemaversion', version,
        description="The version of the schema used in this database.")


def set_backend_type(backend_name):
    """
    Set the schema version stored in the DB. Use only if you know what
    you are doing.
    """
    return set_global_setting(
        'db|backend', backend_name,
        description="The backend used to communicate with the database.")


def check_schema_version():
    """
    Check if the version stored in the database is the same of the version
    of the code. It calls the corresponding version of the selected
    backend.

    :raise ConfigurationError: if the two schema versions do not match.
      Otherwise, just return.
    """
    if settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import check_schema_version
        return check_schema_version()
    elif settings.BACKEND == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.utils import check_schema_version
        return check_schema_version()
    else:
        raise Exception("unknown backend {}".format(settings.BACKEND))


def get_current_profile():
    """
    Return, as a string, the current profile being used.

    Return None if load_dbenv has not been loaded yet.
    """

    if is_dbenv_loaded():
        return settings.AIIDADB_PROFILE
    else:
        return None


