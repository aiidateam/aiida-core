# -*- coding: utf-8 -*-

import logging
import os

import django

from aiida.backends import settings
from aiida.backends.utils import is_dbenv_loaded
from aiida.utils.logger import get_dblogger_extra

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0.1"
__authors__ = "The AiiDA team."


def load_dbenv(process=None, profile=None):
    """
    Load the database environment (Django) and perform some checks.

    :param process: the process that is calling this command ('verdi', or
        'daemon')
    :param profile: the string with the profile to use. If not specified,
        use the default one specified in the AiiDA configuration file.
    """
    _load_dbenv_noschemacheck(process, profile)
    # Check schema version and the existence of the needed tables
    check_schema_version()


def _load_dbenv_noschemacheck(process, profile):
    """
    Load the database environment (Django) WITHOUT CHECKING THE SCHEMA VERSION.
    :param process: the process that is calling this command ('verdi', or
        'daemon')
    :param profile: the string with the profile to use. If not specified,
        use the default one specified in the AiiDA configuration file.

    This should ONLY be used internally, inside load_dbenv, and for schema
    migrations. DO NOT USE OTHERWISE!
    """
    # This function does not use process and profile because they are read
    # from global variables (set before by load_profile) inside the
    # djsite.settings.settings module.
    os.environ['DJANGO_SETTINGS_MODULE'] = 'aiida.backends.djsite.settings.settings'
    django.setup()


def get_current_profile():
    """
    Return, as a string, the current profile being used.

    Return None if load_dbenv has not been loaded yet.
    """

    if is_dbenv_loaded():
        return settings.AIIDADB_PROFILE
    else:
        return None


class DBLogHandler(logging.Handler):
    def emit(self, record):
        from django.core.exceptions import ImproperlyConfigured

        try:
            from aiida.backends.djsite.db.models import DbLog

            DbLog.add_from_logrecord(record)

        except ImproperlyConfigured:
            # Probably, the logger was called without the
            # Django settings module loaded. Then,
            # This ignore should be a no-op.
            pass
        except Exception:
            # To avoid loops with the error handler, I just print.
            # Hopefully, though, this should not happen!
            import traceback

            traceback.print_exc()


def get_log_messages(obj):
    from aiida.backends.djsite.db.models import DbLog
    import json

    extra = get_dblogger_extra(obj)
    # convert to list, too
    log_messages = list(DbLog.objects.filter(**extra).order_by('time').values(
        'loggername', 'levelname', 'message', 'metadata', 'time'))

    # deserialize metadata
    for log in log_messages:
        log.update({'metadata': json.loads(log['metadata'])})

    return log_messages


def get_configured_user_email():
    """
    Return the email (that is used as the username) configured during the
    first verdi install.
    """
    from aiida.common.exceptions import ConfigurationError
    from aiida.common.setup import get_profile_config, DEFAULT_USER_CONFIG_FIELD
    from aiida.backends import settings

    try:
        profile_conf = get_profile_config(settings.AIIDADB_PROFILE,
                                          set_test_location=False)
        email = profile_conf[DEFAULT_USER_CONFIG_FIELD]
    # I do not catch the error in case of missing configuration, because
    # it is already a ConfigurationError
    except KeyError:
        raise ConfigurationError("No 'default_user' key found in the "
                                 "AiiDA configuration file".format(DEFAULT_USER_CONFIG_FIELD))
    return email


def get_daemon_user():
    """
    Return the username (email) of the user that should run the daemon,
    or the default AiiDA user in case no explicit configuration is found
    in the DbSetting table.
    """
    from aiida.common.globalsettings import get_global_setting
    from aiida.common.setup import DEFAULT_AIIDA_USER

    try:
        return get_global_setting('daemon|user')
    except KeyError:
        return DEFAULT_AIIDA_USER


def set_daemon_user(user_email):
    """
    Set the username (email) of the user that is allowed to run the daemon.
    """
    from aiida.common.globalsettings import set_global_setting

    set_global_setting('daemon|user', user_email,
                       description="The only user that is allowed to run the "
                                   "AiiDA daemon on this DB instance")

_aiida_autouser_cache = None



def get_automatic_user():
    """
    Return the default user for this installation of AiiDA.
    """
    global _aiida_autouser_cache

    if _aiida_autouser_cache is not None:
        return _aiida_autouser_cache

    from django.core.exceptions import ObjectDoesNotExist
    from aiida.backends.djsite.db.models import DbUser
    from aiida.common.exceptions import ConfigurationError

    email = get_configured_user_email()

    try:
        _aiida_autouser_cache = DbUser.objects.get(email=email)
        return _aiida_autouser_cache
    except ObjectDoesNotExist:
        raise ConfigurationError("No aiida user with email {}".format(
            email))


def long_field_length():
    """
    Return the length of "long" fields.
    This is used, for instance, for the 'key' field of attributes.
    This returns 1024 typically, but it returns 255 if the backend is mysql.

    :note: Call this function only AFTER having called load_dbenv!
    """
    # One should not load directly settings because there are checks inside
    # for the current profile. However, this function is going to be called
    # only after having loaded load_dbenv, so there should be no problem
    from django.conf import settings

    if 'mysql' in settings.DATABASES['default']['ENGINE']:
        return 255
    else:
        return 1024


def get_db_schema_version():
    """
    Get the current schema version stored in the DB. Return None if
    it is not stored.
    """
    from aiida.common.globalsettings import get_global_setting

    try:
        return get_global_setting('db|schemaversion')
    except KeyError:
        return None


def set_db_schema_version(version):
    """
    Set the schema version stored in the DB. Use only if you know what
    you are doing.
    """
    from aiida.common.globalsettings import set_global_setting

    return set_global_setting('db|schemaversion', version, description=
    "The version of the schema used in this "
    "database.")


def check_schema_version():
    """
    Check if the version stored in the database is the same of the version
    of the code.

    :note: if the DbSetting table does not exist, this function does not
      fail. The reason is to avoid to have problems before running the first
      migrate call.

    :note: if no version is found, the version is set to the version of the
      code. This is useful to have the code automatically set the DB version
      at the first code execution.

    :raise ConfigurationError: if the two schema versions do not match.
      Otherwise, just return.
    """
    import aiida.backends.djsite.db.models
    from django.db import connection
    from aiida.common.exceptions import ConfigurationError

    # Do not do anything if the table does not exist yet
    if 'db_dbsetting' not in connection.introspection.table_names():
        return

    code_schema_version = aiida.backends.djsite.db.models.SCHEMA_VERSION
    db_schema_version = get_db_schema_version()

    if db_schema_version is None:
        # No code schema defined yet, I set it to the code version
        set_db_schema_version(code_schema_version)
        db_schema_version = get_db_schema_version()

    if code_schema_version != db_schema_version:
        raise ConfigurationError(
            "The code schema version is {}, but the version stored in the"
            "database (DbSetting table) is {}, stopping.\n"
            "To migrate to latest version, go to aiida.backends.djsite and run:\n"
            "python manage.py --aiida-profile={} migrate".
            format(code_schema_version, db_schema_version,
                   get_current_profile())
        )
