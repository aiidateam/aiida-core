# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module
"""Utility functions specific to the SqlAlchemy backend."""
import json
from typing import TypedDict


class PsqlConfig(TypedDict, total=False):
    """Configuration to connect to a PostgreSQL database."""
    database_hostname: str
    database_port: int
    database_username: str
    database_password: str
    database_name: str

    engine_kwargs: dict
    """keyword argument that will be passed on to the SQLAlchemy engine."""


def create_sqlalchemy_engine(config: PsqlConfig):
    """Create SQLAlchemy engine (to be used for QueryBuilder queries)

    :param kwargs: keyword arguments that will be passed on to `sqlalchemy.create_engine`.
        See https://docs.sqlalchemy.org/en/13/core/engines.html?highlight=create_engine#sqlalchemy.create_engine for
        more info.
    """
    from sqlalchemy import create_engine

    # The hostname may be `None`, which is a valid value in the case of peer authentication for example. In this case
    # it should be converted to an empty string, because otherwise the `None` will be converted to string literal "None"
    hostname = config['database_hostname'] or ''
    separator = ':' if config['database_port'] else ''

    engine_url = 'postgresql://{user}:{password}@{hostname}{separator}{port}/{name}'.format(
        separator=separator,
        user=config['database_username'],
        password=config['database_password'],
        hostname=hostname,
        port=config['database_port'],
        name=config['database_name']
    )
    return create_engine(
        engine_url,
        json_serializer=json.dumps,
        json_deserializer=json.loads,
        future=True,
        encoding='utf-8',
        **config.get('engine_kwargs', {}),
    )


def create_scoped_session_factory(engine, **kwargs):
    """Create scoped SQLAlchemy session factory"""
    from sqlalchemy.orm import scoped_session, sessionmaker
    return scoped_session(sessionmaker(bind=engine, future=True, **kwargs))


def flag_modified(instance, key):
    """Wrapper around `sqlalchemy.orm.attributes.flag_modified` to correctly dereference utils.ModelWrapper

    Since SqlAlchemy 1.2.12 (and maybe earlier but not in 1.0.19) the flag_modified function will check that the
    key is actually present in the instance or it will except. If we pass a model instance, wrapped in the ModelWrapper
    the call will raise an InvalidRequestError. In this function that wraps the flag_modified of SqlAlchemy, we
    derefence the model instance if the passed instance is actually wrapped in the ModelWrapper.
    """
    from sqlalchemy.orm.attributes import flag_modified as flag_modified_sqla

    from aiida.storage.psql_dos.orm.utils import ModelWrapper

    if isinstance(instance, ModelWrapper):
        instance = instance._model  # pylint: disable=protected-access

    flag_modified_sqla(instance, key)


def install_tc(session):
    """
    Install the transitive closure table with SqlAlchemy.
    """
    from sqlalchemy import text

    links_table_name = 'db_dblink'
    links_table_input_field = 'input_id'
    links_table_output_field = 'output_id'
    closure_table_name = 'db_dbpath'
    closure_table_parent_field = 'parent_id'
    closure_table_child_field = 'child_id'

    session.execute(
        text(
            get_pg_tc(
                links_table_name, links_table_input_field, links_table_output_field, closure_table_name,
                closure_table_parent_field, closure_table_child_field
            )
        )
    )


def get_pg_tc(
    links_table_name, links_table_input_field, links_table_output_field, closure_table_name, closure_table_parent_field,
    closure_table_child_field
):
    """
    Return the transitive closure table template
    """
    from string import Template

    pg_tc = Template(
        """

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

"""
    )
    return pg_tc.substitute(
        links_table_name=links_table_name,
        links_table_input_field=links_table_input_field,
        links_table_output_field=links_table_output_field,
        closure_table_name=closure_table_name,
        closure_table_parent_field=closure_table_parent_field,
        closure_table_child_field=closure_table_child_field
    )
