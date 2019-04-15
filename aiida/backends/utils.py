# -*- coding: utf-8 -*-

from __future__ import absolute_import

from aiida.backends import settings
from aiida.backends.profile import load_profile, is_profile_loaded
from aiida.common.exceptions import ConfigurationError, InvalidOperation


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.6.0.1"

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

    if settings.BACKEND == "sqlalchemy":
        # Maybe schema version should be also checked for SQLAlchemy version.
        from aiida.backends.sqlalchemy.utils \
            import load_dbenv as load_dbenv_sqlalchemy
        return load_dbenv_sqlalchemy(
            process=process, profile=profile, *args, **kwargs)
    elif settings.BACKEND == "django":
        from aiida.backends.djsite.utils import load_dbenv as load_dbenv_django
        return load_dbenv_django(
            process=process, profile=profile, *args, **kwargs)
    else:
        raise ConfigurationError("Invalid settings.BACKEND: {}".format(
            settings.BACKEND))


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
