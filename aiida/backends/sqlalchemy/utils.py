# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

from alembic import command
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory

from sqlalchemy.orm.exc import NoResultFound

from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy import get_scoped_session
from aiida.backends.utils import validate_attribute_key, SettingsManager, Setting, validate_schema_generation
from aiida.common import NotExistent


ALEMBIC_FILENAME = 'alembic.ini'
ALEMBIC_REL_PATH = 'migrations'


class SqlaSettingsManager(SettingsManager):
    """Class to get, set and delete settings from the `DbSettings` table."""

    table_name = 'db_dbsetting'

    def validate_table_existence(self):
        """Verify that the `DbSetting` table actually exists.

        :raises: `~aiida.common.exceptions.NotExistent` if the settings table does not exist
        """
        from sqlalchemy.engine import reflection
        inspector = reflection.Inspector.from_engine(get_scoped_session().bind)
        if self.table_name not in inspector.get_table_names():
            raise NotExistent('the settings table does not exist')

    def get(self, key):
        """Return the setting with the given key.

        :param key: the key identifying the setting
        :return: Setting
        :raises: `~aiida.common.exceptions.NotExistent` if the settings does not exist
        """
        from aiida.backends.sqlalchemy.models.settings import DbSetting
        self.validate_table_existence()

        try:
            setting = get_scoped_session().query(DbSetting).filter_by(key=key).one()
        except NoResultFound:
            raise NotExistent('setting `{}` does not exist'.format(key))

        return Setting(key, setting.getvalue(), setting.description, setting.time)

    def set(self, key, value, description=None):
        """Return the settings with the given key.

        :param key: the key identifying the setting
        :param value: the value for the setting
        :param description: optional setting description
        """
        from aiida.backends.sqlalchemy.models.settings import DbSetting
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
        from aiida.backends.sqlalchemy.models.settings import DbSetting
        self.validate_table_existence()

        try:
            setting = get_scoped_session().query(DbSetting).filter_by(key=key).one()
            setting.delete()
        except NoResultFound:
            raise NotExistent('setting `{}` does not exist'.format(key))


def flag_modified(instance, key):
    """Wrapper around `sqlalchemy.orm.attributes.flag_modified` to correctly dereference utils.ModelWrapper

    Since SqlAlchemy 1.2.12 (and maybe earlier but not in 1.0.19) the flag_modified function will check that the
    key is actually present in the instance or it will except. If we pass a model instance, wrapped in the ModelWrapper
    the call will raise an InvalidRequestError. In this function that wraps the flag_modified of SqlAlchemy, we
    derefence the model instance if the passed instance is actually wrapped in the ModelWrapper.
    """
    from sqlalchemy.orm.attributes import flag_modified as flag_modified_sqla
    from aiida.orm.implementation.sqlalchemy.utils import ModelWrapper

    if isinstance(instance, ModelWrapper):
        instance = instance._model

    flag_modified_sqla(instance, key)


def load_dbenv(profile):
    """Load the database environment and ensure that the code and database schema versions are compatible.

    :param profile: the string with the profile to use
    """
    _load_dbenv_noschemacheck(profile)
    check_schema_version(profile_name=profile.name)


def _load_dbenv_noschemacheck(profile):
    """Load the database environment without checking that code and database schema versions are compatible.

    This should ONLY be used internally, inside load_dbenv, and for schema migrations. DO NOT USE OTHERWISE!

    :param profile: instance of `Profile` whose database to load
    """
    sa.reset_session(profile)


def unload_dbenv():
    """Unload the database environment, which boils down to destroying the current engine and session."""
    if sa.ENGINE is not None:
        sa.ENGINE.dispose()
    sa.SCOPED_SESSION_CLASS = None


def migrate_database(alembic_cfg=None):
    """Migrate the database to the latest schema version.

    :param config: alembic configuration to use, will use default if not provided
    """
    validate_schema_generation()
    from aiida.backends import sqlalchemy as sa

    if alembic_cfg is None:
        alembic_cfg = get_alembic_conf()

    with sa.ENGINE.connect() as connection:
        alembic_cfg.attributes['connection'] = connection
        command.upgrade(alembic_cfg, 'head')


def check_schema_version(profile_name):
    """
    Check if the version stored in the database is the same of the version of the code.

    :raise aiida.common.ConfigurationError: if the two schema versions do not match
    """
    from aiida.backends import sqlalchemy as sa
    from aiida.common.exceptions import ConfigurationError

    alembic_cfg = get_alembic_conf()

    validate_schema_generation()

    # Getting the version of the code and the database, reusing the existing engine (initialized by AiiDA)
    with sa.ENGINE.begin() as connection:
        alembic_cfg.attributes['connection'] = connection
        schema_version_code = get_migration_head(alembic_cfg)
        schema_version_database = get_db_schema_version(alembic_cfg)

    schema_version_database = validate_schema_generation(schema_version_code, schema_version_database)

    if schema_version_code != schema_version_database:
        kwargs = {
            'schema_version_database': schema_version_database,
            'schema_version_code': schema_version_code,
            'profile_name': profile_name
        }
        raise ConfigurationError(
            'Database schema version {schema_version_database} is outdated compared to the code schema version '
            '{schema_version_code}\nBefore you upgrade, make sure all calculations and workflows have finished running.'
            '\nIf this is not the case, revert the code to the previous version and finish them first.\n'
            'To migrate the database to the current version, run the following commands:'
            '\n  verdi -p {profile_name} daemon stop\n  verdi -p {profile_name} database migrate'.format(**kwargs))


SCHEMA_VERSION_RESET = '91b573400be5'


def validate_schema_generation(schema_version_code, schema_version_database):
    """Validate that the current database schema generation."""
    from distutils.version import StrictVersion
    from aiida.common.exceptions import ConfigurationError
    from ..schema import get_schema_generation, update_schema_generation, SCHEMA_GENERATION_VALUE

    schema_generation_current = get_schema_generation()
    schema_generation_required = StrictVersion(SCHEMA_GENERATION_VALUE)
    schema_version_reset = SCHEMA_VERSION_RESET

    if schema_generation_current < schema_generation_required and schema_version_database != schema_version_reset:
        raise ConfigurationError(
            'Database schema version {} is outdated and belongs to the previous generation.\nTo start using this version '
            'of `aiida-core`, you have to first install `aiida-core==1.0.0` and perform the migration.\nThen you can '
            'reinstall this version of `aiida-core` and continue your work.'.format(
                schema_version_database))

    if schema_generation_current < schema_generation_required:
        reset_schema_version(schema_version_code)
        update_schema_generation()

    return schema_version_code


def reset_schema_version(schema_version):
    """Reset the schema version."""
    from aiida.manage.manager import get_manager
    backend = get_manager()._load_backend(schema_check=False)  # pylint: disable=protected-access
    backend.execute_raw(r"""UPDATE alembic_version SET version_num='{}';""".format(schema_version))


def get_migration_head(config):
    """
    This function returns the head of the migration scripts.
    :param config: The alembic configuration.
    :return: The version of the head.
    """
    script = ScriptDirectory.from_config(config)
    return script.get_current_head()


def get_db_schema_version(config):
    """
    This function returns the current version of the database.
    :param config: The alembic configuration.
    :return: The version of the database.
    """
    if config is None:
        return None

    script = ScriptDirectory.from_config(config)

    def get_db_version(rev, _):
        if isinstance(rev, tuple) and len(rev) > 0:
            config.attributes['rev'] = rev[0]
        else:
            config.attributes['rev'] = None

        return []

    with EnvironmentContext(
        config,
        script,
        fn=get_db_version
    ):
        script.run_env()
        return config.attributes['rev']


def get_alembic_conf():
    """
    This function returns the alembic configuration file contents by doing
    the necessary updates in the 'script_location' name.
    :return: The alembic configuration.
    """
    # Constructing the alembic full path & getting the configuration
    import os
    dir_path = os.path.dirname(os.path.realpath(__file__))
    alembic_fpath = os.path.join(dir_path, ALEMBIC_FILENAME)
    alembic_cfg = Config(alembic_fpath)

    # Set the alembic script directory location
    alembic_dpath = os.path.join(dir_path, ALEMBIC_REL_PATH)
    alembic_cfg.set_main_option('script_location', alembic_dpath)

    return alembic_cfg


def delete_nodes_and_connections_sqla(pks_to_delete):
    """
    Delete all nodes corresponding to pks in the input.
    :param pks_to_delete: A list, tuple or set of pks that should be deleted.
    """
    from aiida.backends import sqlalchemy as sa
    from aiida.backends.sqlalchemy.models.node import DbNode, DbLink
    from aiida.backends.sqlalchemy.models.group import table_groups_nodes
    from aiida.manage.manager import get_manager

    backend = get_manager().get_backend()

    with backend.transaction() as session:
        # I am first making a statement to delete the membership of these nodes to groups.
        # Since table_groups_nodes is a sqlalchemy.schema.Table, I am using expression language to compile
        # a stmt to be executed by the session. It works, but it's not nice that two different ways are used!
        # Can this be changed?
        stmt = table_groups_nodes.delete().where(table_groups_nodes.c.dbnode_id.in_(list(pks_to_delete)))
        session.execute(stmt)
        # First delete links, then the Nodes, since we are not cascading deletions.
        # Here I delete the links coming out of the nodes marked for deletion.
        session.query(DbLink).filter(DbLink.input_id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')
        # Here I delete the links pointing to the nodes marked for deletion.
        session.query(DbLink).filter(DbLink.output_id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')
        # Now I am deleting the nodes
        session.query(DbNode).filter(DbNode.id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')
