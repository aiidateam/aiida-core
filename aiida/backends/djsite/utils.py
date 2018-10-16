# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This modules contains a number of utility functions specific to the
Django backend.
"""

from __future__ import absolute_import
import os
import django
from aiida.common.log import get_dblogger_extra


def load_dbenv(profile=None):
    """
    Load the database environment (Django) and perform some checks.

    :param profile: the string with the profile to use. If not specified,
        use the default one specified in the AiiDA configuration file.
    """
    _load_dbenv_noschemacheck(profile)
    # Check schema version and the existence of the needed tables
    check_schema_version(profile)


def _load_dbenv_noschemacheck(profile):  # pylint: disable=unused-argument
    """
    Load the database environment (Django) WITHOUT CHECKING THE SCHEMA VERSION.

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


def get_log_messages(obj):
    """
    Get a list of log messages from the database for the given
    object (typically a Node)

    :param obj: the object (typically a Node) for which you want to get
        a list of DbLog messages
    :return: a list of log messages. Each log message is a dictionary
        including a 'loggername', a 'levelname', a 'message', a 'time' at
        which the log message was issued, as well as additional 'metadata'
    """
    from aiida.backends.djsite.db.models import DbLog
    import json

    extra = get_dblogger_extra(obj)

    # convert to list, too
    log_messages = list(
        DbLog.objects.filter(**extra).order_by('time').values('loggername', 'levelname', 'message', 'metadata', 'time'))

    # deserialize metadata
    for log in log_messages:
        log.update({'metadata': json.loads(log['metadata'])})

    return log_messages


_aiida_autouser_cache = None  # pylint: disable=invalid-name


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

    # else
    return 1024


def check_schema_version(profile):
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

    filepath_utils = os.path.abspath(__file__)
    filepath_manage = os.path.join(os.path.dirname(filepath_utils), 'manage.py')

    if profile is None:
        from aiida.common.setup import get_default_profile_name
        profile = get_default_profile_name()

    if code_schema_version != db_schema_version:
        raise ConfigurationError("The code schema version is {}, but the version stored in the "
                                 "database (DbSetting table) is {}, stopping.\n"
                                 "To migrate the database to the current version, run the following commands:"
                                 "\n  verdi daemon stop\n  python {} --aiida-profile={} migrate".format(
                                     code_schema_version, db_schema_version, filepath_manage, profile))


def set_db_schema_version(version):
    """
    Set the schema version stored in the DB. Use only if you know what
    you are doing.
    """
    from aiida.backends.utils import set_global_setting
    return set_global_setting(
        'db|schemaversion', version, description="The version of the schema used in this database.")


def get_db_schema_version():
    """
    Get the current schema version stored in the DB. Return None if
    it is not stored.
    """
    from aiida.backends.utils import get_global_setting
    try:
        return get_global_setting('db|schemaversion')
    except KeyError:
        return None


def delete_nodes_and_connections_django(pks_to_delete):  # pylint: disable=invalid-name
    """
    Delete all nodes corresponding to pks in the input.
    :param pks_to_delete: A list, tuple or set of pks that should be deleted.
    """
    from django.db import transaction
    from django.db.models import Q
    from aiida.backends.djsite.db import models
    with transaction.atomic():
        # This is fixed in pylint-django>=2, but this supports only py3
        # pylint: disable=no-member
        # Delete all links pointing to or from a given node
        models.DbLink.objects.filter(Q(input__in=pks_to_delete) | Q(output__in=pks_to_delete)).delete()
        # now delete nodes
        models.DbNode.objects.filter(pk__in=pks_to_delete).delete()


def pass_to_django_manage(argv, profile=None):
    """
    Call the corresponding django manage.py command
    """
    from aiida.backends.utils import load_dbenv as load_dbenv_, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv_(profile=profile)

    from django.core import management
    management.execute_from_command_line(argv)
