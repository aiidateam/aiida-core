# -*- coding: utf-8 -*-

from __future__ import absolute_import

from aiida.backends import settings
from aiida.backends.profile import load_profile, is_profile_loaded
from aiida.common.exceptions import ConfigurationError, InvalidOperation


def is_dbenv_loaded():
    """
    Return True of the dbenv was already loaded (with a call to load_dbenv),
    False otherwise.
    """
    return settings.LOAD_DBENV_CALLED


def load_dbenv(*args, **kwargs):
    # check if profile is loaded
    if not is_profile_loaded():
        load_profile(profile=settings.AIIDADB_PROFILE)

    if is_dbenv_loaded():
        raise InvalidOperation("You cannot call load_dbenv multiple times!")
    settings.LOAD_DBENV_CALLED = True

    if settings.BACKEND == "sqlalchemy":
        from aiida.backends.sqlalchemy.utils \
            import load_dbenv as load_dbenv_sqlalchemy
        return load_dbenv_sqlalchemy(*args, **kwargs)
    elif settings.BACKEND == "django":
        from aiida.backends.djsite.utils import load_dbenv as load_dbenv_django
        return load_dbenv_django(*args, **kwargs)
    else:
        raise ConfigurationError("Invalid settings.BACKEND: {}".format(
            settings.BACKEND))
    ######################
    # Check schema version
    ######################


def get_automatic_user():
    if settings.BACKEND == "sqlalchemy":
        from aiida.backends.sqlalchemy.utils import (
            get_automatic_user as get_automatic_user_sqla)
        return get_automatic_user_sqla()
    elif settings.BACKEND == "django":
        from aiida.backends.djsite.utils import (
            get_automatic_user as get_automatic_user_dj)
        return get_automatic_user_dj()
    else:
        raise ValueError("This method doesn't exist for this backend")


def get_group_list(*args, **kwargs):
    if settings.BACKEND == "sqlalchemy":
        raise ValueError("This method doesn't exist for this backend")
    elif settings.BACKEND == "django":
        from aiida.backends.djsite.cmdline import (
            get_group_list as get_group_list_dj)
        return get_group_list_dj(*args, **kwargs)
    else:
        raise ValueError("This method doesn't exist for this backend")


def get_workflow_list(*args, **kwargs):
    if settings.BACKEND == "sqlalchemy":
        raise ValueError("This method doesn't exist for this backend")
    elif settings.BACKEND == "django":
        from aiida.backends.djsite.cmdline import (
            get_workflow_list as get_workflow_list_dj)
        return get_workflow_list_dj(*args, **kwargs)
    else:
        raise ValueError("This method doesn't exist for this backend")


def get_log_messages(*args, **kwargs):
    if settings.BACKEND == "sqlalchemy":
        raise ValueError("This method doesn't exist for this backend")
    elif settings.BACKEND == "django":
        from aiida.backends.djsite.cmdline import (
            get_log_messages as get_log_messages_dj)
        return get_log_messages_dj(*args, **kwargs)
    else:
        raise ValueError("This method doesn't exist for this backend")
