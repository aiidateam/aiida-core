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
from __future__ import absolute_import
from __future__ import print_function
try:
    import ultrajson as json
    from functools import partial

    # double_precision = 15, to replicate what PostgreSQL numerical type is
    # using
    json_dumps = partial(json.dumps, double_precision=15)
    json_loads = partial(json.loads, precise_float=True)
except ImportError:
    from aiida.common import json

    json_dumps = json.dumps
    json_loads = json.loads

import datetime
import re

import six
from alembic import command
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from dateutil import parser
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from aiida.backends import sqlalchemy as sa

ALEMBIC_FILENAME = "alembic.ini"
ALEMBIC_REL_PATH = "migrations"


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


def recreate_after_fork(engine):
    """
    :param engine: the engine that will be used by the sessionmaker

    Callback called after a fork. Not only disposes the engine, but also recreates a new scoped session
    to use independent sessions in the forked process.
    """
    sa.engine.dispose()
    sa.scopedsessionclass = scoped_session(sessionmaker(bind=sa.engine, expire_on_commit=True))


def reset_session(config):
    """
    :param config: the configuration of the profile from the
       configuration file

    Resets (global) engine and sessionmaker classes, to create a new one
    (or creates a new one from scratch if not already available)
    """
    from multiprocessing.util import register_after_fork

    engine_url = (
        "postgresql://{AIIDADB_USER}:{AIIDADB_PASS}@"
        "{AIIDADB_HOST}{sep}{AIIDADB_PORT}/{AIIDADB_NAME}"
        ).format(sep=':' if config['AIIDADB_PORT'] else '', **config)

    sa.engine = create_engine(engine_url, json_serializer=dumps_json,
                              json_deserializer=loads_json, encoding='utf-8')
    sa.scopedsessionclass = scoped_session(sessionmaker(bind=sa.engine,
                                                        expire_on_commit=True))
    register_after_fork(sa.engine, recreate_after_fork)


def load_dbenv(profile=None, connection=None):
    """
    Load the database environment (SQLAlchemy) and perform some checks.

    :param profile: the string with the profile to use. If not specified,
        use the default one specified in the AiiDA configuration file.
    """
    _load_dbenv_noschemacheck(profile=profile)
    # Check schema version and the existence of the needed tables
    check_schema_version(profile_name=profile)


def _load_dbenv_noschemacheck(profile=None, connection=None):
    """
    Load the SQLAlchemy database.
    """
    from aiida.manage.configuration import get_config

    config = get_config()
    profile = config.current_profile
    reset_session(profile.dictionary)


_aiida_autouser_cache = None


def dumps_json(d):
    """
    Transforms all datetime object into isoformat and then returns the JSON
    """

    def f(v):
        if isinstance(v, list):
            return [f(_) for _ in v]
        elif isinstance(v, dict):
            return dict((key, f(val)) for key, val in v.items())
        elif isinstance(v, datetime.datetime):
            return v.isoformat()
        return v

    return json_dumps(f(d))


date_reg = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+(\+\d{2}:\d{2})?$')


def loads_json(s):
    """
    Loads the json and try to parse each basestring as a datetime object
    """

    ret = json_loads(s)

    def f(d):
        if isinstance(d, list):
            for i, val in enumerate(d):
                d[i] = f(val)
            return d
        elif isinstance(d, dict):
            for k, v in d.items():
                d[k] = f(v)
            return d
        elif isinstance(d, six.string_types):
            if date_reg.match(d):
                try:
                    return parser.parse(d)
                except (ValueError, TypeError):
                    return d
            return d
        return d

    return f(ret)


# XXX the code here isn't different from the one use in Django. We may be able
# to refactor it in some way
def install_tc(session):
    """
    Install the transitive closure table with SqlAlchemy.
    """
    links_table_name = "db_dblink"
    links_table_input_field = "input_id"
    links_table_output_field = "output_id"
    closure_table_name = "db_dbpath"
    closure_table_parent_field = "parent_id"
    closure_table_child_field = "child_id"

    session.execute(get_pg_tc(links_table_name, links_table_input_field,
                              links_table_output_field, closure_table_name,
                              closure_table_parent_field,
                              closure_table_child_field))


def get_pg_tc(links_table_name,
              links_table_input_field,
              links_table_output_field,
              closure_table_name,
              closure_table_parent_field,
              closure_table_child_field):
    """
    Return the transitive closure table template
    """
    from string import Template

    pg_tc = Template("""

DROP TRIGGER IF EXISTS autoupdate_tc ON $links_table_name;
DROP FUNCTION IF EXISTS update_tc();

CREATE OR REPLACE FUNCTION update_tc()
  RETURNS trigger AS
$$BODY$$
DECLARE

    new_id INTEGER;
    old_id INTEGER;
    num_rows INTEGER;

BEGIN

  IF tg_op = 'INSERT' THEN

    IF EXISTS (
      SELECT Id FROM $closure_table_name
      WHERE $closure_table_parent_field = new.$links_table_input_field
         AND $closure_table_child_field = new.$links_table_output_field
         AND depth = 0
         )
    THEN
      RETURN null;
    END IF;

    IF new.$links_table_input_field = new.$links_table_output_field
    OR EXISTS (
      SELECT id FROM $closure_table_name
        WHERE $closure_table_parent_field = new.$links_table_output_field
        AND $closure_table_child_field = new.$links_table_input_field
        )
    THEN
      RETURN null;
    END IF;

    INSERT INTO $closure_table_name (
         $closure_table_parent_field,
         $closure_table_child_field,
         depth)
      VALUES (
         new.$links_table_input_field,
         new.$links_table_output_field,
         0);

    new_id := lastval();

    UPDATE $closure_table_name
      SET entry_edge_id = new_id
        , exit_edge_id = new_id
        , direct_edge_id = new_id
      WHERE id = new_id;


    INSERT INTO $closure_table_name (
      entry_edge_id,
      direct_edge_id,
      exit_edge_id,
      $closure_table_parent_field,
      $closure_table_child_field,
      depth)
      SELECT id
         , new_id
         , new_id
         , $closure_table_parent_field
         , new.$links_table_output_field
         , depth + 1
        FROM $closure_table_name
        WHERE $closure_table_child_field = new.$links_table_input_field;


    INSERT INTO $closure_table_name (
      entry_edge_id,
      direct_edge_id,
      exit_edge_id,
      $closure_table_parent_field,
      $closure_table_child_field,
      depth)
      SELECT new_id
        , new_id
        , id
        , new.$links_table_input_field
        , $closure_table_child_field
        , depth + 1
        FROM $closure_table_name
        WHERE $closure_table_parent_field = new.$links_table_output_field;

    INSERT INTO $closure_table_name (
      entry_edge_id,
      direct_edge_id,
      exit_edge_id,
      $closure_table_parent_field,
      $closure_table_child_field,
      depth)
      SELECT A.id
        , new_id
        , B.id
        , A.$closure_table_parent_field
        , B.$closure_table_child_field
        , A.depth + B.depth + 2
     FROM $closure_table_name A
        CROSS JOIN $closure_table_name B
     WHERE A.$closure_table_child_field = new.$links_table_input_field
       AND B.$closure_table_parent_field = new.$links_table_output_field;

  END IF;

  IF tg_op = 'DELETE' THEN

    IF NOT EXISTS(
        SELECT id FROM $closure_table_name
        WHERE $closure_table_parent_field = old.$links_table_input_field
        AND $closure_table_child_field = old.$links_table_output_field AND
        depth = 0 )
    THEN
        RETURN NULL;
    END IF;

    CREATE TABLE PurgeList (Id int);

    INSERT INTO PurgeList
      SELECT id FROM $closure_table_name
          WHERE $closure_table_parent_field = old.$links_table_input_field
        AND $closure_table_child_field = old.$links_table_output_field AND
        depth = 0;

    WHILE (1 = 1)
    loop

      INSERT INTO PurgeList
        SELECT id FROM $closure_table_name
          WHERE depth > 0
          AND ( entry_edge_id IN ( SELECT Id FROM PurgeList )
          OR direct_edge_id IN ( SELECT Id FROM PurgeList )
          OR exit_edge_id IN ( SELECT Id FROM PurgeList ) )
          AND Id NOT IN (SELECT Id FROM PurgeList );

      GET DIAGNOSTICS num_rows = ROW_COUNT;
      if (num_rows = 0) THEN
        EXIT;
      END IF;
    end loop;

    DELETE FROM $closure_table_name WHERE Id IN ( SELECT Id FROM PurgeList);
    DROP TABLE PurgeList;

  END IF;

  RETURN NULL;

END
$$BODY$$
  LANGUAGE plpgsql VOLATILE
  COST 100;


CREATE TRIGGER autoupdate_tc
  AFTER INSERT OR DELETE OR UPDATE
  ON $links_table_name FOR each ROW
  EXECUTE PROCEDURE update_tc();

""")
    return pg_tc.substitute(links_table_name=links_table_name,
                            links_table_input_field=links_table_input_field,
                            links_table_output_field=links_table_output_field,
                            closure_table_name=closure_table_name,
                            closure_table_parent_field=closure_table_parent_field,
                            closure_table_child_field=closure_table_child_field)


def migrate_database(alembic_cfg=None):
    """Migrate the database to the latest schema version.

    :param config: alembic configuration to use, will use default if not provided
    """
    from aiida.backends import sqlalchemy as sa

    if alembic_cfg is None:
        alembic_cfg = get_alembic_conf()

    with sa.engine.connect() as connection:
        alembic_cfg.attributes['connection'] = connection
        command.upgrade(alembic_cfg, "head")


def check_schema_version(profile_name=None):
    """
    Check if the version stored in the database is the same of the version of the code.

    :raise aiida.common.ConfigurationError: if the two schema versions do not match
    """
    from aiida.backends import sqlalchemy as sa
    from aiida.backends.settings import IN_DOC_MODE
    from aiida.common.exceptions import ConfigurationError

    # Early exit if we compile the documentation since the schema check is not needed and it creates problems
    # with the sqlalchemy migrations
    if IN_DOC_MODE:
        return

    alembic_cfg = get_alembic_conf()

    # Getting the version of the code and the database, reusing the existing engine (initialized by AiiDA)
    with sa.engine.begin() as connection:
        alembic_cfg.attributes['connection'] = connection
        code_schema_version = get_migration_head(alembic_cfg)
        db_schema_version = get_db_schema_version(alembic_cfg)

    if code_schema_version != db_schema_version:
        from aiida.manage.manager import get_manager
        manager = get_manager()
        profile_name = manager.get_profile().name
        raise ConfigurationError('Database schema version {} is outdated compared to the code schema version {}\n'
                                 'To migrate the database to the current version, run the following commands:'
                                 '\n  verdi -p {} daemon stop\n  verdi -p {} database migrate'.format(
                                    code_schema_version, db_schema_version, profile_name, profile_name))



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

    session = sa.get_scoped_session()
    try:
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
        # Here I commit this scoped session!
        session.commit()
    except Exception as e:
        # If there was any exception, I roll back the session.
        session.rollback()
        raise e
    finally:
        session.close()
