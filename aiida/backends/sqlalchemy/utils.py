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


def delete_nodes_and_connections_sqla(pks_to_delete):  # pylint: disable=invalid-name
    """
    Delete all nodes corresponding to pks in the input.
    :param pks_to_delete: A list, tuple or set of pks that should be deleted.
    """
    # pylint: disable=no-value-for-parameter
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
        instance = instance._model  # pylint: disable=protected-access

    flag_modified_sqla(instance, key)


def install_tc(session):
    """
    Install the transitive closure table with SqlAlchemy.
    """
    links_table_name = 'db_dblink'
    links_table_input_field = 'input_id'
    links_table_output_field = 'output_id'
    closure_table_name = 'db_dbpath'
    closure_table_parent_field = 'parent_id'
    closure_table_child_field = 'child_id'

    session.execute(
        get_pg_tc(
            links_table_name, links_table_input_field, links_table_output_field, closure_table_name,
            closure_table_parent_field, closure_table_child_field
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
