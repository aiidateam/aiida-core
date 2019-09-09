# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-name-in-module,no-member,import-error,cyclic-import
"""Utility functions specific to the Django backend."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import django

from aiida.backends.utils import validate_attribute_key, SettingsManager, Setting
from aiida.common import NotExistent

SCHEMA_VERSION_DB_KEY = 'db|schemaversion'
SCHEMA_VERSION_DB_DESCRIPTION = 'The version of the schema used in this database.'


class DjangoSettingsManager(SettingsManager):
    """Class to get, set and delete settings from the `DbSettings` table."""

    table_name = 'db_dbsetting'

    def validate_table_existence(self):
        """Verify that the `DbSetting` table actually exists.

        :raises: `~aiida.common.exceptions.NotExistent` if the settings table does not exist
        """
        from django.db import connection
        if self.table_name not in connection.introspection.table_names():
            raise NotExistent('the settings table does not exist')

    def get(self, key):
        """Return the setting with the given key.

        :param key: the key identifying the setting
        :return: Setting
        :raises: `~aiida.common.exceptions.NotExistent` if the settings does not exist
        """
        from aiida.backends.djsite.db.models import DbSetting

        self.validate_table_existence()
        setting = DbSetting.objects.filter(key=key).first()

        if setting is None:
            raise NotExistent('setting `{}` does not exist'.format(key))

        return Setting(setting.key, setting.val, setting.description, setting.time)

    def set(self, key, value, description=None):
        """Return the settings with the given key.

        :param key: the key identifying the setting
        :param value: the value for the setting
        :param description: optional setting description
        """
        from aiida.backends.djsite.db.models import DbSetting

        self.validate_table_existence()
        validate_attribute_key(key)

        other_attribs = dict()
        if description is not None:
            other_attribs['description'] = description

        DbSetting.set_value(key, value, other_attribs=other_attribs)

    def delete(self, key):
        """Delete the setting with the given key.

        :param key: the key identifying the setting
        :raises: `~aiida.common.exceptions.NotExistent` if the settings does not exist
        """
        from aiida.backends.djsite.db.models import DbSetting

        self.validate_table_existence()

        try:
            DbSetting.del_value(key=key)
        except KeyError:
            raise NotExistent('setting `{}` does not exist'.format(key))


def load_dbenv(profile):
    """Load the database environment and ensure that the code and database schema versions are compatible.

    :param profile: instance of `Profile` whose database to load
    """
    _load_dbenv_noschemacheck(profile)
    check_schema_version(profile_name=profile.name)


def _load_dbenv_noschemacheck(profile):  # pylint: disable=unused-argument
    """Load the database environment without checking that code and database schema versions are compatible.

    This should ONLY be used internally, inside load_dbenv, and for schema migrations. DO NOT USE OTHERWISE!

    :param profile: instance of `Profile` whose database to load
    """
    os.environ['DJANGO_SETTINGS_MODULE'] = 'aiida.backends.djsite.settings'
    django.setup()


def unload_dbenv():
    """Unload the database environment.

    This means that the settings in `aiida.backends.djsite.settings` are "unset".
    This needs to implemented and will address #2813
    """


_aiida_autouser_cache = None  # pylint: disable=invalid-name


def migrate_database():
    """Migrate the database to the latest schema version."""
    from django.core.management import call_command
    call_command('migrate')


def check_schema_version(profile_name):
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
        raise ConfigurationError(
            'Database schema version {} is outdated compared to the code schema version {}\n'
            'Before you upgrade, make sure all calculations and workflows have finished running.\n'
            'If this is not the case, revert the code to the previous version and finish them first.\n'
            'To migrate the database to the current version, run the following commands:'
            '\n  verdi -p {} daemon stop\n  verdi -p {} database migrate'.format(
                db_schema_version, code_schema_version, profile_name, profile_name
            )
        )


def set_db_schema_version(version):
    """
    Set the schema version stored in the DB. Use only if you know what you are doing.
    """
    from aiida.backends.utils import get_settings_manager
    manager = get_settings_manager()
    return manager.set(SCHEMA_VERSION_DB_KEY, version, description=SCHEMA_VERSION_DB_DESCRIPTION)


def get_db_schema_version():
    """
    Get the current schema version stored in the DB. Return None if
    it is not stored.
    """
    from django.db.utils import ProgrammingError
    from aiida.manage.manager import get_manager
    backend = get_manager()._load_backend(schema_check=False)  # pylint: disable=protected-access

    try:
        result = backend.execute_raw(r"""SELECT tval FROM db_dbsetting WHERE key = 'db|schemaversion';""")
    except ProgrammingError:
        result = backend.execute_raw(r"""SELECT val FROM db_dbsetting WHERE key = 'db|schemaversion';""")

    return result[0][0]


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
