# -*- coding: utf-8 -*-

import ujson
# import simplejson as json
import datetime
from dateutil import parser

import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aiida.common.exceptions import InvalidOperation, ConfigurationError
from aiida.common.setup import (get_profile_config, DEFAULT_USER_CONFIG_FIELD)

from aiida.backends import sqlalchemy, settings
from aiida.backends.profile import (is_profile_loaded,
                                    load_profile)

def is_dbenv_loaded():
    """
    Return if the environment has already been loaded or not.
    """
    return sqlalchemy.session is not None


def load_dbenv(process=None, profile=None, connection=None):
    """
    Load the SQLAlchemy database.
    """
    if settings.LOAD_DBENV_CALLED:
        raise InvalidOperation("You cannot call load_dbenv multiple times!")
    settings.LOAD_DBENV_CALLED = True

    if not is_profile_loaded():
        load_profile(process, profile)

    config = get_profile_config(settings.AIIDADB_PROFILE)

    # Those import are necessary for SQLAlchemy to correvtly detect the models
    # These should be on top of the file, but because of a circular import they need to be
    # here...
    from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
    from aiida.backends.sqlalchemy.models.calcstate import DbCalcState
    from aiida.backends.sqlalchemy.models.comment import DbComment
    from aiida.backends.sqlalchemy.models.computer import DbComputer
    from aiida.backends.sqlalchemy.models.group import DbGroup
    from aiida.backends.sqlalchemy.models.lock import DbLock
    from aiida.backends.sqlalchemy.models.log import DbLog
    from aiida.backends.sqlalchemy.models.node import DbLink, DbNode, DbPath
    from aiida.backends.sqlalchemy.models.user import DbUser
    from aiida.backends.sqlalchemy.models.workflow import DbWorkflow, DbWorkflowData, DbWorkflowStep

    if not connection:
        engine_url = ("postgresql://{AIIDADB_USER}:{AIIDADB_PASS}@"
                      "{AIIDADB_HOST}:{AIIDADB_PORT}/{AIIDADB_NAME}").format(**config)
        engine = create_engine(engine_url,
                               json_serializer=dumps_json,
                               json_deserializer=loads_json)
        Session = sessionmaker(bind=engine)
        sqlalchemy.session = Session()
    else:
        Session = sessionmaker()
        sqlalchemy.session = Session(bind=connection)

_aiida_autouser_cache = None

def get_automatic_user():
    global _aiida_autouser_cache

    if _aiida_autouser_cache is not None:
        return _aiida_autouser_cache

    from aiida.backends.sqlalchemy.models.user import DbUser

    email = get_configured_user_email()

    _aiida_autouser_cache = DbUser.query.filter(DbUser.email == email).first()

    if not _aiida_autouser_cache:
        raise ConfigurationError("No aiida user with email {}".format(
            email))
    return _aiida_autouser_cache

def get_configured_user_email():
    """
    Return the email (that is used as the username) configured during the
    first verdi install.
    """
    try:
        profile_conf = get_profile_config(settings.AIIDADB_PROFILE,
                                          set_test_location=False)
        email = profile_conf[DEFAULT_USER_CONFIG_FIELD]
    # I do not catch the error in case of missing configuration, because
    # it is already a ConfigurationError
    except KeyError:
        raise ConfigurationError("No 'default_user' key found in the "
                                 "AiiDA configuration file")
    return email


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

    # return json.dumps(f(d))
    return ujson.dumps(f(d), double_precision=15)

date_reg = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+(\+\d{2}:\d{2})?$')

def loads_json(s):
    """
    Loads the json and try to parse each basestring as a datetime object
    """

    # TODO: use the object_hook mecanism instead ?
    # ret = json.loads(s)
    ret = ujson.loads(s)

    def f(d):
        if isinstance(d, list):
            return [f(_) for _ in d]
        elif isinstance(d, dict):
            for k, v in d.iteritems():
                d[k] = f(v)
            return d
        elif isinstance(d, basestring):
            # XXX: it might be faster to first check with a precompiled regex
            # that the date is in a parsable format.
            if date_reg.match(d)
                try:
                    return parser.parse(d)
                except (ValueError, TypeError):
                    return d
            return d
        return d

    return f(ret)


def install_tc(session):
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
