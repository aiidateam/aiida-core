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
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import django

# pylint: disable=no-name-in-module, no-member, import-error


def load_dbenv(profile=None):
    """
    Load the database environment (Django) and perform some checks.

    :param profile: the string with the profile to use. If not specified,
        use the default one specified in the AiiDA configuration file.
    """
    _load_dbenv_noschemacheck(profile)
    # Check schema version and the existence of the needed tables
    check_schema_version(profile_name=profile)


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


_aiida_autouser_cache = None  # pylint: disable=invalid-name


def migrate_database():
    """Migrate the database to the latest schema version."""
    from django.core.management import call_command
    call_command('migrate')


def check_schema_version(profile_name=None):
    """
    Check if the version stored in the database is the same of the version
    of the code.

    :note: if the DbSetting table does not exist, this function does not
      fail. The reason is to avoid to have problems before running the first
      migrate call.

    :note: if no version is found, the version is set to the version of the
      code. This is useful to have the code automatically set the DB version
      at the first code execution.

    :raise aiida.common.ConfigurationError: if the two schema versions do not match.
      Otherwise, just return.
    """
    # pylint: disable=duplicate-string-formatting-argument
    from django.db import connection

    import aiida.backends.djsite.db.models
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
        if profile_name is None:
            from aiida.manage.manager import get_manager
            manager = get_manager()
            profile_name = manager.get_profile().name

        raise ConfigurationError('Database schema version {} is outdated compared to the code schema version {}\n'
                                 'To migrate the database to the current version, run the following commands:'
                                 '\n  verdi -p {} daemon stop\n  verdi -p {} database migrate'.format(
                                     db_schema_version, code_schema_version, profile_name, profile_name))


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
