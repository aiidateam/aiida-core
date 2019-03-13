# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
import gc
import getpass
import math
import os
import sys

from six.moves import range

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql.json import JSON
from sqlalchemy.engine import reflection
from sqlalchemy.orm import relationship, subqueryload, load_only
from sqlalchemy.schema import Column
from sqlalchemy.sql.expression import func
from sqlalchemy.types import Integer, String, Boolean, DateTime, Text, Float

import aiida.common.setup as setup
from aiida import is_dbenv_loaded
from aiida.backends import sqlalchemy as sa
from aiida.backends.profile import BACKEND_SQLA
from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.utils import flag_modified
from aiida.manage.backup.backup_utils import query_yes_no


# Profile keys
aiidadb_backend_key = "AIIDADB_BACKEND"

# Profile values
aiidadb_backend_value_sqla = "sqlalchemy"


"""
This scipt transitions an Django database 0.6.0 to an SQLAlchemy
database 0.7.0. It also updates the needed config files.

It is supposed to be executed via ipython in the following way:

from aiida.backends.sqlalchemy.transition import transition
transition(profile="your_profile",group_size=10000)
"""


# Table name definitions
NODE_TABLE_NAME = "db_dbnode"
ATTR_TABLE_NAME = "db_dbattribute"
EXTRAS_TABLE_NAME = "db_dbextra"
SETTINGS_TABLE_NAME= "db_dbsetting"

# Column name definitions
ATTR_COL_NAME = "attributes"
EXTRAS_COL_NAME = "extras"
SETTINGS_VAL_COL_NAME = "val"


def attributes_to_dict(attr_list):
    """
    Transform the attributes of a node into a dictionary. It assumes the key
    are ordered alphabetically, and that they all belong to the same node.
    """
    d = {}

    error = False
    for a in attr_list:
        try:
            tmp_d = select_from_key(a.key, d)
        except Exception:
            print("Couldn't transfer attribute {} with key {} for dbnode {}"
                  .format(a.id, a.key, a.dbnode_id))
            error = True
            continue
        key = a.key.split('.')[-1]

        if key.isdigit():
            key = int(key)

        dt = a.datatype

        if dt == "dict":
            tmp_d[key] = {}
        elif dt == "list":
            tmp_d[key] = [None] * a.ival
        else:
            val = None
            if dt == "txt":
                val = a.tval
            elif dt == "float":
                val = a.fval
                if math.isnan(val):
                    val = 'NaN'
            elif dt == "int":
                val = a.ival
            elif dt == "bool":
                val = a.bval
            elif dt == "date":
                val = a.dval

            tmp_d[key] = val

    return (d, error)


def select_from_key(key, d):
    """
    Return element of the dict to do the insertion on. If it is foo.1.bar, it
    will return d["foo"][1]. If it is only foo, it will return d directly.
    """
    path = key.split('.')[:-1]

    tmp_d = d
    for p in path:
        if p.isdigit():
            tmp_d = tmp_d[int(p)]
        else:
            tmp_d = tmp_d[p]

    return tmp_d


def modify_link_table():

    session = sa.get_scoped_session()

    with session.begin(subtransactions=True):
        print("\nStaring the modification of link table.")

        inspector = reflection.Inspector.from_engine(session.bind)
        table_cols = inspector.get_columns("db_dblink")
        col_type_list = [_["type"] for _ in table_cols if _["name"] == "type"]
        if len(col_type_list) == 0:
            print("Creating link type column")
            session.execute('ALTER TABLE db_dblink ADD COLUMN '
                               'type varchar(255)')
        else:
            print("Link type column already exists.")
    session.commit()


def transition_extras(profile=None, group_size=1000, delete_table=False):
    """
    Migrate the DbExtra table into the extras column for db_dbnode.
    """
    if not is_dbenv_loaded():
        transition_load_db_env(profile=profile)

    class DbExtra(Base):
        """
        DbExtra table, use only for migration purposes.
        """
        __tablename__ = EXTRAS_TABLE_NAME

        id = Column(Integer, primary_key=True)

        key = Column(String(1024), nullable=False)
        datatype = Column(String(10), nullable=False)

        tval = Column(Text, nullable=False)
        fval = Column(Float)
        ival = Column(Integer)
        bval = Column(Boolean)
        dval = Column(DateTime(timezone=True))

        dbnode_id = Column(Integer, ForeignKey('db_dbnode.id'), nullable=False)
        dbnode = relationship('DbNode', backref='old_extras')

    print("\nStarting migration of extras.")

    inspector = reflection.Inspector.from_engine(sa.get_scoped_session().bind)

    table_names = inspector.get_table_names()
    if NODE_TABLE_NAME not in table_names:
        raise Exception("There is no {} table in the database. Transition"
                        "to SQLAlchemy can not be done. Exiting."
                        .format(NODE_TABLE_NAME))

    node_table_cols = inspector.get_columns(NODE_TABLE_NAME)
    col_names = [_["name"] for _ in node_table_cols]

    if EXTRAS_COL_NAME in col_names:
        print("Column named {} found at the {} table of the database. I assume "
              "that the migration of the extras has already been done and "
              "therefore I proceed with the next migration step."
              .format(EXTRAS_COL_NAME, NODE_TABLE_NAME))
        return

    session = sa.get_scoped_session()

    with session.begin(subtransactions=True):
        print("Creating columns..")
        session.execute('ALTER TABLE db_dbnode ADD COLUMN extras '
                           'JSONB DEFAULT \'{}\'')
        from aiida.backends.sqlalchemy.models.node import DbNode
        total_nodes = session.query(func.count(DbNode.id)).scalar()

        total_groups = int(math.ceil(total_nodes/group_size))
        error = False

        for i in range(total_groups):

            print("Migrating group {} of {}".format(i, total_groups))
            nodes = DbNode.query.options(
                subqueryload('old_extras'), load_only('id', 'extras')
            ).order_by(DbNode.id)[i*group_size:(i+1)*group_size]

            for node in nodes:
                attrs, err_ = attributes_to_dict(sorted(node.old_extras,
                                                        key=lambda a: a.key))
                error |= err_

                node.extras = attrs
                session.add(node)

            session.flush()
            session.expunge_all()

        if error:
            cont = query_yes_no("There has been some errors during the "
                                "migration. Do you want to continue?", "no")
            if not cont:
                session.rollback()
                sys.exit(-1)
        if delete_table:
            session.execute('DROP TABLE db_dbextra')
    session.commit()
    print("Migration of extras finished.")


def transition_attributes(profile=None, group_size=1000, debug=False,
                          delete_table=False):
    """
    Migrate the DbAttribute table into the attributes column of db_dbnode.
    """
    if not is_dbenv_loaded():
        transition_load_db_env(profile=profile)

    class DbAttribute(Base):
        """
        DbAttribute table, use only for migration purposes.
        """
        __tablename__ = ATTR_TABLE_NAME

        id = Column(Integer, primary_key=True)

        key = Column(String(1024), nullable=False)
        datatype = Column(String(10), nullable=False)

        tval = Column(Text, nullable=False)
        fval = Column(Float)
        ival = Column(Integer)
        bval = Column(Boolean)
        dval = Column(DateTime(timezone=True))

        dbnode_id = Column(Integer, ForeignKey('db_dbnode.id'), nullable=False)
        dbnode = relationship('DbNode', backref='old_attrs')

    print("\nStarting migration of attributes")

    inspector = reflection.Inspector.from_engine(sa.get_scoped_session().bind)

    table_names = inspector.get_table_names()
    if NODE_TABLE_NAME not in table_names:
        raise Exception("There is no {} table in the database. Transition"
                        "to SQLAlchemy can not be done. Exiting"
                        .format(NODE_TABLE_NAME))

    node_table_cols = inspector.get_columns(NODE_TABLE_NAME)
    col_names = [_["name"] for _ in node_table_cols]

    if ATTR_COL_NAME in col_names:
        print("Column named {} found at the {} table of the database. I assume "
              "that the migration of the attributes has already been done and "
              "therefore I proceed with the next migration step."
              .format(ATTR_COL_NAME, NODE_TABLE_NAME))
        return

    session = sa.get_scoped_session()

    with session.begin(subtransactions=True):
        print("Creating columns..")
        session.execute('ALTER TABLE db_dbnode ADD COLUMN attributes '
                           'JSONB DEFAULT \'{}\'')
        from aiida.backends.sqlalchemy.models.node import DbNode
        total_nodes = session.query(func.count(DbNode.id)).scalar()

        total_groups = int(math.ceil(total_nodes/group_size))
        error = False

        for i in range(total_groups):
            print("Migrating group {} of {}".format(i, total_groups))

            nodes = DbNode.query.options(
                subqueryload('old_attrs'), load_only('id', 'attributes')
            ).order_by(DbNode.id)[i*group_size:(i+1)*group_size]

            for node in nodes:
                attrs, err_ = attributes_to_dict(sorted(node.old_attrs,
                                                        key=lambda a: a.key))
                error |= err_

                node.attributes = attrs
                session.add(node)

            # Remove the db_dbnode from sqlalchemy, to allow the GC to do its
            # job.
            session.flush()
            session.expunge_all()

            del nodes
            gc.collect()

        if error:
            cont = query_yes_no("There has been some errors during the "
                                "migration. Do you want to continue?", "no")
            if not cont:
                session.rollback()
                sys.exit(-1)
        if delete_table:
            session.execute('DROP TABLE db_dbattribute')
    session.commit()
    print("Migration of attributes finished.")


def transition_settings(profile=None):
    """
    Migrate the DbAttribute table into the attributes column of db_dbnode.
    """
    if not is_dbenv_loaded():
        transition_load_db_env(profile=profile)

    from aiida.common import timezone

    class DbSetting(Base):
        __tablename__ = "db_dbsetting"
        id = Column(Integer, primary_key=True)

        key = Column(String(255), index=True, nullable=False)
        datatype = Column(String(10), index=True, nullable=False)

        tval = Column(String(255), default='', nullable=True)
        fval = Column(Float, default=None, nullable=True)
        ival = Column(Integer, default=None, nullable=True)
        bval = Column(Boolean, default=None, nullable=True)
        dval = Column(DateTime(timezone=True), default=None, nullable=True)
        val = Column(JSONB, default={})

        description = Column(String(255), default='', nullable=True)
        time = Column(DateTime(timezone=True), default=timezone.now)

    print("\nStarting migration of settings.")

    inspector = reflection.Inspector.from_engine(sa.get_scoped_session().bind)

    settings_table_cols = inspector.get_columns(SETTINGS_TABLE_NAME)
    col_names = [_["name"] for _ in settings_table_cols]

    if SETTINGS_VAL_COL_NAME in col_names:
        print("Column named {} found at the {} table of the database. I assume "
              "that the migration of the attributes has already been done and "
              "therefore I proceed with the next migration step."
              .format(SETTINGS_VAL_COL_NAME, SETTINGS_TABLE_NAME))
        return

    session = sa.get_scoped_session()

    with session.begin(subtransactions=True):
        print("Creating columns..")
        session.execute('ALTER TABLE db_dbsetting ADD COLUMN val '
                           'JSONB DEFAULT \'{}\'')
    session.commit()

    with session.begin(subtransactions=True):
        total_settings = session.query(DbSetting).all()

        for settings in total_settings:

            dt = settings.datatype
            val = None
            if dt == "txt":
                val = settings.tval
            elif dt == "float":
                val = settings.fval
                if math.isnan(val):
                    val = 'NaN'
            elif dt == "int":
                val = settings.ival
            elif dt == "bool":
                val = settings.bval
            elif dt == "date":
                val = settings.dval

            settings.val = val
            flag_modified(settings, "val")
            session.flush()

    session.commit()

    with session.begin(subtransactions=True):
        for col_name in ["datatype", "tval", "fval", "ival", "bval", "dval"]:
            sql = ("ALTER TABLE {table} DROP COLUMN {column}")
            session.execute(sql.format(table=SETTINGS_TABLE_NAME,
                                          column=col_name))

    session.commit()
    print("Migration of settings finished.")


def transition_json_column(profile=None):
    """
    Migrate the TEXT column containing JSON into JSON columns
    """

    print("\nChanging various columns to JSON format.")

    if not is_dbenv_loaded():
        transition_load_db_env(profile=profile)

    table_col = [
        ('db_dbauthinfo', 'metadata'),
        ('db_dbauthinfo', 'auth_params'),
        ('db_dbcomputer', 'metadata'),
        ('db_dbcomputer', 'transport_params'),
        ('db_dblog', 'metadata')
    ]

    inspector = reflection.Inspector.from_engine(sa.get_scoped_session().bind)

    sql = ("ALTER TABLE {table} ALTER COLUMN {column} TYPE JSONB "
           "USING {column}::JSONB")

    session = sa.get_scoped_session()

    with session.begin(subtransactions=True):

        for table, col in table_col:
            table_cols = inspector.get_columns(table)
            col_type_list = [_["type"] for _ in table_cols if _["name"] == col]
            if len(col_type_list) != 1:
                raise Exception("Problem with table {} and column {}. Either"
                                "the column doesn't exist or multiple "
                                "occurrences were found.".format(table, col))

            if isinstance(col_type_list[0], JSON):
                print("Column {} of table {} is already in JSON format. "
                      "Proceeding with the next table & column."
                      .format(col, table))
                continue

            print("Changing column {} of table {} in JSON format."
                  .format(table, col))
            session.execute(sql.format(table=table, column=col))

    session.commit()


def create_gin_index():
    """
    Create the GIN index for the attributes column of db_dbnode.
    """
    print("\nChecking if GIN indexes have to be created.")
    inspector = reflection.Inspector.from_engine(sa.get_scoped_session().bind)
    db_node_idx = inspector.get_indexes("db_dbnode")
    db_node_idx_names = [_["name"] for _ in db_node_idx]
    if "db_dbnode_attributes_idx" not in db_node_idx_names:
        print("Creating db_dbnode_attributes_idx on db_node.")
        sa.get_scoped_session().bind.execute("CREATE INDEX db_dbnode_attributes_idx ON "
                                "db_dbnode USING gin(attributes)")
    else:
        print("db_dbnode_attributes_idx on db_node already exists.")


def transition_load_db_env(profile=None, *args, **kwargs):
    from aiida.backends.profile import load_profile
    from aiida.backends import settings
    from aiida.backends.sqlalchemy.utils import _load_dbenv_noschemacheck

    settings.LOAD_DBENV_CALLED = True

    # This is going to set global variables in settings, including
    # settings.BACKEND
    load_profile(profile=profile)

    _load_dbenv_noschemacheck(profile=profile)


def set_correct_schema_version_and_backend():
    from aiida.common import timezone
    # Setting the correct backend and schema version
    SQLA_SCHEMA_VERSION = 0.1

    session = sa.get_scoped_session()

    with session.begin(subtransactions=True):
        # Setting manually the correct schema version
        session.execute(
            'DELETE FROM db_dbsetting WHERE key=\'db|schemaversion\'')
        session.execute(
            'INSERT INTO db_dbsetting (key, val, description, time) values '
            '(\'db|schemaversion\', \'{}\', '
            '\'The version of the schema used in this database.\', \'{}\')'
                .format(SQLA_SCHEMA_VERSION, timezone.datetime.now()))

        # Setting the correct backend
        session.execute('DELETE FROM db_dbsetting WHERE key=\'db|backend\'')
        session.execute(
            'INSERT INTO db_dbsetting (key, val, description, time) values '
            '(\'db|backend\', \'"{}"\', '
            '\'The backend used to communicate with database.\', \'{}\')'
                .format(BACKEND_SQLA, timezone.datetime.now()))
    session.commit()


def transition_db(profile=None, group_size=1000, delete_table=False):
    """
    Migrate the attributes, extra, and some other columns to use JSONMigrate
    the attributes, extra, and some other columns to use JSONB column type.
    """
    cont = query_yes_no("Starting complete database transition. Be sure to "
                        "backup your database before continuing, and that no "
                        "one else is using it. Do you want to continue?", "no")
    if not cont:
        print("Answered no. Exiting")
        sys.exit(0)

    transition_attributes(profile=profile, group_size=group_size,
                          delete_table=delete_table)

    transition_extras(profile=profile,group_size=group_size,
                      delete_table=delete_table)

    create_gin_index()

    modify_link_table()

    transition_settings(profile=profile)

    transition_json_column(profile=profile)

    set_correct_schema_version_and_backend()

    print("\nDatabase transition finished.")


def change_backend_to_sqla(profile=None):
    """
    Gets the main AiiDA configuration and searches if there is a backend
    defined. If there isn't any then Django is added.
    """
    # Get the available configuration
    conf = setup.get_config()  # Profile key

    _profiles_key = "profiles"

    # Identifying all the available profiles
    if _profiles_key in conf.keys():
        profiles = conf[_profiles_key]

        if profile not in profiles.keys():
            print("The provided profile name is not one of the available "
                  "profiles. Exiting")
            sys.exit(0)
        curr_profile = profiles[profile]

        if aiidadb_backend_key in curr_profile.keys():
            if curr_profile[aiidadb_backend_key] == aiidadb_backend_value_sqla:
                print("This is already an SQLAlchemy profile. Exiting")
                sys.exit(0)
            curr_profile[aiidadb_backend_key] = \
                aiidadb_backend_value_sqla
        else:
            print("No backend entry found in your configuration file. Are you "
                  "sure that you are running a version 0.6.*?")
            sys.exit(0)

    # Returning the configuration
    return conf


def transition_config_files(profile=None):

    print("Changing backend from Django to SQLAlchemy in config files")

    # Backup the previous config
    setup.backup_config()
    # Get the AiiDA directory path
    aiida_directory = os.path.expanduser(setup.AIIDA_CONFIG_FOLDER)
    # Construct the log directory path
    log_dir = os.path.join(aiida_directory, setup.LOG_SUBDIR)
    # Update the configuration if needed
    confs = change_backend_to_sqla(profile)
    # Store the configuration
    setup.store_config(confs)
    # Construct the daemon directory path
    daemon_dir = os.path.join(aiida_directory, setup.DAEMON_SUBDIR)
    # Update the daemon directory
    setup.install_daemon_files(aiida_directory, daemon_dir, log_dir,
                               getpass.getuser())

    print("Config file update finished.")


def transition(profile=None, group_size=1000, delete_table=False):

    transition_config_files(profile)
    print("Proceeding to database tarbnsition.")
    transition_db(profile, group_size, delete_table)
    print("\nTransition finished")



