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
import datetime
import re

from aiida.backends import BACKEND_SQLA, BACKEND_DJANGO
from aiida.common.exceptions import ConfigurationError
from aiida.manage import configuration
from dateutil import parser
from aiida.common.exceptions import ValidationError, NotExistent

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


def datetime_to_isoformat(v):
    """
    Transforms all datetime object into isoformat and then returns the final object.
    """
    if isinstance(v, list):
        return [datetime_to_isoformat(_) for _ in v]
    elif isinstance(v, dict):
        return dict((key, datetime_to_isoformat(val)) for key, val in v.items())
    elif isinstance(v, datetime.datetime):
        return v.isoformat()
    return v


date_reg = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+(\+\d{2}:\d{2})?$')


def isoformat_to_datetime(d):
    """
    Parses each basestring as a datetime object and if it suceeds, converts it.
    """
    if isinstance(d, list):
        for i, val in enumerate(d):
            d[i] = isoformat_to_datetime(val)
        return d
    elif isinstance(d, dict):
        for k, v in d.items():
            d[k] = isoformat_to_datetime(v)
        return d
    elif isinstance(d, six.string_types):
        if date_reg.match(d):
            try:
                return parser.parse(d)
            except (ValueError, TypeError):
                return d
        return d
    return d


# The separator for sub-fields (for JSON stored values).Keys are not allowed
# to contain the separator even if the
_sep = "."


def validate_key(key):
    """
    Validate the key string to check if it is valid (e.g., if it does not
    contain the separator symbol.).

    :return: None if the key is valid
    :raise aiida.common.ValidationError: if the key is not valid
    """
    if not isinstance(key, six.string_types):
        raise ValidationError("The key must be a string.")
    if not key:
        raise ValidationError("The key cannot be an empty string.")
    if _sep in key:
        raise ValidationError("The separator symbol '{}' cannot be present "
                              "in the key of this field.".format(_sep))


def get_value_of_sub_field(key, original_get_value):
    """
    Get the value that corresponds to sub-fields of dictionaries stored in a
    JSON. For example, if there is a dictionary {'b': 'c'} stored as value of
    the key 'a'
    value 'a'
    :param key: The key that can be simple, a string, or complex, a set of keys
    separated by the separator value.
    :param original_get_value: The function that should be called to get the
    original value (which can be a dictionary too).
    :return: The value that correspond to the complex (or not) key.
    :raise aiida.common.NotExistent: If the key doesn't correspond to a value
    """
    keys = list()
    if _sep in key:
        keys.extend(key.split(_sep))
    else:
        keys.append(key)

    if len(keys) == 1:
        return original_get_value(keys[0])
    else:
        try:
            curr_val = original_get_value(keys[0])
            curr_pos = 1
            while curr_pos < len(keys):
                curr_val = curr_val[keys[curr_pos]]
                curr_pos += 1

            return curr_val
        except TypeError:
            raise NotExistent("The sub-field {} doesn't correspond "
                              "to a value.".format(key))
