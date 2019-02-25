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

import six

from aiida.backends import settings
from aiida.backends.profile import load_profile, BACKEND_SQLA, BACKEND_DJANGO
from aiida.common.exceptions import ConfigurationError, NotExistent, InvalidOperation

AIIDA_ATTRIBUTE_SEP = '.'


def validate_attribute_key(key):
    """
    Validate the key string to check if it is valid (e.g., if it does not
    contain the separator symbol.).

    :return: None if the key is valid
    :raise aiida.common.ValidationError: if the key is not valid
    """
    from aiida.common.exceptions import ValidationError

    if not isinstance(key, six.string_types):
        raise ValidationError("The key must be a string.")
    if not key:
        raise ValidationError("The key cannot be an empty string.")
    if AIIDA_ATTRIBUTE_SEP in key:
        raise ValidationError("The separator symbol '{}' cannot be present "
                              "in the key of attributes, extras, etc.".format(
            AIIDA_ATTRIBUTE_SEP))


def is_dbenv_loaded():
    """
    Return True of the dbenv was already loaded (with a call to load_dbenv),
    False otherwise.
    """
    return settings.LOAD_DBENV_CALLED


def load_dbenv(profile=None, *args, **kwargs):
    if is_dbenv_loaded():
        raise InvalidOperation("You cannot call load_dbenv multiple times!")

    # This is going to set global variables in settings, including settings.BACKEND
    load_profile(profile=profile)

    if settings.BACKEND == BACKEND_SQLA:
        # Maybe schema version should be also checked for SQLAlchemy version.
        from aiida.backends.sqlalchemy.utils \
            import load_dbenv as load_dbenv_sqlalchemy
        to_return = load_dbenv_sqlalchemy(profile=profile, *args, **kwargs)
    elif settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import load_dbenv as load_dbenv_django
        to_return = load_dbenv_django(profile=profile, *args, **kwargs)
    else:
        raise ConfigurationError("Invalid settings.BACKEND: {}".format(
            settings.BACKEND))

    settings.LOAD_DBENV_CALLED = True
    return to_return


def _load_dbenv_noschemacheck(profile=None, *args, **kwargs):
    if is_dbenv_loaded():
        raise InvalidOperation("You cannot call load_dbenv multiple times!")

    # This is going to set global variables in settings, including settings.BACKEND
    load_profile(profile=profile)

    if settings.BACKEND == BACKEND_SQLA:
        # Maybe schema version should be also checked for SQLAlchemy version.
        from aiida.backends.sqlalchemy.utils \
            import _load_dbenv_noschemacheck as _load_dbenv_noschemacheck_sqlalchemy
        to_return = _load_dbenv_noschemacheck_sqlalchemy(profile=profile, *args, **kwargs)
    elif settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import _load_dbenv_noschemacheck as _load_dbenv_noschemacheck_django
        to_return = _load_dbenv_noschemacheck_django(profile=profile, *args, **kwargs)
    else:
        raise ConfigurationError("Invalid settings.BACKEND: {}".format(
            settings.BACKEND))

    settings.LOAD_DBENV_CALLED = True
    return to_return


def get_global_setting(key):
    if settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.globalsettings import get_global_setting
    elif settings.BACKEND == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.globalsettings import get_global_setting
    else:
        raise Exception("unknown backend {}".format(settings.BACKEND))

    return get_global_setting(key)


def get_global_setting_description(key):
    if settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.globalsettings import get_global_setting_description
    elif settings.BACKEND == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.globalsettings import get_global_setting_description
    else:
        raise Exception("unknown backend {}".format(settings.BACKEND))

    return get_global_setting_description(key)


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


def del_global_setting(key):
    if settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.globalsettings import del_global_setting
    elif settings.BACKEND == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.globalsettings import del_global_setting
    else:
        raise Exception("unknown backend {}".format(settings.BACKEND))

    del_global_setting(key)


def set_backend_type(backend_name):
    """
    Set the schema version stored in the DB. Use only if you know what
    you are doing.
    """
    return set_global_setting(
        'db|backend', backend_name,
        description="The backend used to communicate with the database.")


def get_current_profile():
    """
    Return, as a string, the current profile being used.

    Return None if load_dbenv has not been loaded yet.
    """

    if is_dbenv_loaded():
        return settings.AIIDADB_PROFILE
    else:
        return None


def delete_nodes_and_connections(pks):
    if settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import delete_nodes_and_connections_django as delete_nodes_backend
    elif settings.BACKEND == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.utils import delete_nodes_and_connections_sqla as delete_nodes_backend
    else:
        raise Exception("unknown backend {}".format(settings.BACKEND))

    delete_nodes_backend(pks)
