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

from aiida.backends import BACKEND_SQLA, BACKEND_DJANGO
from aiida.common.exceptions import ConfigurationError
from aiida.manage import configuration

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


def load_dbenv(profile=None, *args, **kwargs):
    if configuration.PROFILE.database_backend == BACKEND_SQLA:
        # Maybe schema version should be also checked for SQLAlchemy version.
        from aiida.backends.sqlalchemy.utils \
            import load_dbenv as load_dbenv_sqlalchemy
        to_return = load_dbenv_sqlalchemy(profile=profile, *args, **kwargs)
    elif configuration.PROFILE.database_backend == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import load_dbenv as load_dbenv_django
        to_return = load_dbenv_django(profile=profile, *args, **kwargs)
    else:
        raise ConfigurationError("Invalid configuration.PROFILE.database_backend: {}".format(
            configuration.PROFILE.database_backend))

    return to_return


def _load_dbenv_noschemacheck(profile=None, *args, **kwargs):
    if configuration.PROFILE.database_backend == BACKEND_SQLA:
        # Maybe schema version should be also checked for SQLAlchemy version.
        from aiida.backends.sqlalchemy.utils \
            import _load_dbenv_noschemacheck as _load_dbenv_noschemacheck_sqlalchemy
        to_return = _load_dbenv_noschemacheck_sqlalchemy(profile=profile, *args, **kwargs)
    elif configuration.PROFILE.database_backend == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import _load_dbenv_noschemacheck as _load_dbenv_noschemacheck_django
        to_return = _load_dbenv_noschemacheck_django(profile=profile, *args, **kwargs)
    else:
        raise ConfigurationError("Invalid configuration.PROFILE.database_backend: {}".format(configuration.PROFILE.database_backend))

    return to_return


def get_global_setting(key):
    if configuration.PROFILE.database_backend == BACKEND_DJANGO:
        from aiida.backends.djsite.globalsettings import get_global_setting
    elif configuration.PROFILE.database_backend == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.globalsettings import get_global_setting
    else:
        raise Exception("unknown backend {}".format(configuration.PROFILE.database_backend))

    return get_global_setting(key)


def get_global_setting_description(key):
    if configuration.PROFILE.database_backend == BACKEND_DJANGO:
        from aiida.backends.djsite.globalsettings import get_global_setting_description
    elif configuration.PROFILE.database_backend == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.globalsettings import get_global_setting_description
    else:
        raise Exception("unknown backend {}".format(configuration.PROFILE.database_backend))

    return get_global_setting_description(key)


def get_backend_type():
    """
    Set the schema version stored in the DB. Use only if you know what
    you are doing.
    """
    return get_global_setting('db|backend')


def set_global_setting(key, value, description=None):
    if configuration.PROFILE.database_backend == BACKEND_DJANGO:
        from aiida.backends.djsite.globalsettings import set_global_setting
    elif configuration.PROFILE.database_backend == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.globalsettings import set_global_setting
    else:
        raise Exception("unknown backend {}".format(configuration.PROFILE.database_backend))

    set_global_setting(key, value, description)


def del_global_setting(key):
    if configuration.PROFILE.database_backend == BACKEND_DJANGO:
        from aiida.backends.djsite.globalsettings import del_global_setting
    elif configuration.PROFILE.database_backend == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.globalsettings import del_global_setting
    else:
        raise Exception("unknown backend {}".format(configuration.PROFILE.database_backend))

    del_global_setting(key)


def set_backend_type(backend_name):
    """Set the schema version stored in the DB. Use only if you know what you are doing."""
    return set_global_setting(
        'db|backend', backend_name,
        description="The backend used to communicate with the database.")


def delete_nodes_and_connections(pks):
    if configuration.PROFILE.database_backend == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import delete_nodes_and_connections_django as delete_nodes_backend
    elif configuration.PROFILE.database_backend == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.utils import delete_nodes_and_connections_sqla as delete_nodes_backend
    else:
        raise Exception("unknown backend {}".format(configuration.PROFILE.database_backend))

    delete_nodes_backend(pks)
