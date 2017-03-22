# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################



try:
    import ultrajson as json
    from functools import partial
    # double_precision = 15, to replicate what PostgreSQL numerical type is
    # using
    json_dumps = partial(json.dumps, double_precision=15)
    json_loads = partial(json.loads, precise_float=True)
except ImportError:
    import json
    json_dumps = json.dumps
    json_loads = json.loads

import datetime
from dateutil import parser

import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from aiida.common.exceptions import InvalidOperation, ConfigurationError
from aiida.common.setup import (get_profile_config, DEFAULT_USER_CONFIG_FIELD)

from aiida.backends import sqlalchemy as sa, settings

from aiida.backends.profile import (is_profile_loaded,
                                    load_profile)


# def is_dbenv_loaded():
#     """
#     Return if the environment has already been loaded or not.
#     """
#     return sa.get_scoped_session() is not None

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
        "{AIIDADB_HOST}:{AIIDADB_PORT}/{AIIDADB_NAME}"
    ).format(**config)

    sa.engine = create_engine(engine_url,
                           json_serializer=dumps_json,
                           json_deserializer=loads_json)
    sa.scopedsessionclass = scoped_session(sessionmaker(bind=sa.engine, expire_on_commit=True))
    register_after_fork(sa.engine, recreate_after_fork)


def load_dbenv(process=None, profile=None, connection=None):
    """
    Load the database environment (SQLAlchemy) and perform some checks.

    :param process: the process that is calling this command ('verdi', or
        'daemon')
    :param profile: the string with the profile to use. If not specified,
        use the default one specified in the AiiDA configuration file.
    """
    _load_dbenv_noschemacheck(process=process, profile=profile)
    # Check schema version and the existence of the needed tables
    check_schema_version()


def _load_dbenv_noschemacheck(process=None, profile=None, connection=None):
    """
    Load the SQLAlchemy database.
    """
    config = get_profile_config(settings.AIIDADB_PROFILE)
    reset_session(config)

_aiida_autouser_cache = None


def get_automatic_user():
    from aiida.common.utils import get_configured_user_email
    # global _aiida_autouser_cache

    # if _aiida_autouser_cache is not None:
    #     return _aiida_autouser_cache

    from aiida.backends.sqlalchemy.models.user import DbUser
    from aiida.common.utils import get_configured_user_email
    
    email = get_configured_user_email()

    _aiida_autouser_cache = DbUser.query.filter(DbUser.email == email).first()

    if not _aiida_autouser_cache:
        raise ConfigurationError("No aiida user with email {}".format(
            email))
    return _aiida_autouser_cache


def get_daemon_user():
    """
    Return the username (email) of the user that should run the daemon,
    or the default AiiDA user in case no explicit configuration is found
    in the DbSetting table.
    """
    from aiida.backends.sqlalchemy.globalsettings import get_global_setting
    from aiida.common.setup import DEFAULT_AIIDA_USER

    try:
        return get_global_setting('daemon|user')
    except KeyError:
        return DEFAULT_AIIDA_USER


def set_daemon_user(user_email):
    """
    Return the username (email) of the user that should run the daemon,
    or the default AiiDA user in case no explicit configuration is found
    in the DbSetting table.
    """
    from aiida.backends.sqlalchemy.globalsettings import set_global_setting

    set_global_setting("daemon|user", user_email,
                       description="The only user that is allowed to run the "
                                   "AiiDA daemon on this DB instance")


def dumps_json(d):
    """
    Transforms all datetime object into isoformat and then returns the JSON
    """

    def f(v):
        if isinstance(v, list):
            return [f(_) for _ in v]
        elif isinstance(v, dict):
            return dict((key, f(val)) for key, val in v.iteritems())
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
            for k, v in d.iteritems():
                d[k] = f(v)
            return d
        elif isinstance(d, basestring):
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
    from aiida.common.exceptions import ConfigurationError
    from sqlalchemy.engine import reflection
    from aiida.backends.sqlalchemy.models import SCHEMA_VERSION
    from aiida.backends.utils import (
        get_db_schema_version, set_db_schema_version,get_current_profile)

    # Do not do anything if the table does not exist yet
    inspector = reflection.Inspector.from_engine(sa.get_scoped_session().bind)
    if 'db_dbsetting' not in inspector.get_table_names():
        return

    code_schema_version = SCHEMA_VERSION
    db_schema_version = get_db_schema_version()

    if db_schema_version is None:
        # No code schema defined yet, I set it to the code version
        set_db_schema_version(code_schema_version)
        db_schema_version = get_db_schema_version()

    if code_schema_version != db_schema_version:
        raise ConfigurationError(
            "The code schema version is {}, but the version stored in the"
            "database (DbSetting table) is {}, stopping.\n".
            format(code_schema_version, db_schema_version)
        )
