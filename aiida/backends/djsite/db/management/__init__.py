# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from django.contrib.auth import models as auth_models
from django.conf import settings

#====================================
#   Postgresql Transive Closure
#====================================

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


#====================================
#   Mysql Transive Closure
#====================================

def get_mysql_trigger_update(db_name,
                             links_table_name,
                             links_table_input_field,
                             links_table_output_field,
                             closure_table_name,
                             closure_table_parent_field,
                             closure_table_child_field):
    from string import Template

    trigger_update = Template("""

CREATE TRIGGER update_tc_insert AFTER INSERT ON $links_table_name
FOR EACH ROW
proc_label:BEGIN
      
      DECLARE new_id integer;

      IF ( SELECT 1 = 1 FROM $closure_table_name
           WHERE $closure_table_parent_field = NEW.$links_table_input_field
             AND $closure_table_child_field = NEW.$links_table_output_field
             AND depth = 0 )
      THEN
        LEAVE proc_label;
      END IF;

      IF NEW.$links_table_input_field = NEW.$links_table_output_field
      OR ( SELECT 1=1 FROM $closure_table_name
           WHERE $closure_table_parent_field = NEW.$links_table_output_field
           AND $closure_table_child_field = NEW.$links_table_input_field)
      THEN
        LEAVE proc_label;
      END IF;
    
      #START TRANSACTION ;
      INSERT INTO $closure_table_name ( $closure_table_parent_field, $closure_table_child_field, depth)
      VALUES ( NEW.$links_table_input_field, NEW.$links_table_output_field, 0);

      SET new_id = LAST_INSERT_ID();

      UPDATE $closure_table_name
      SET entry_edge_id = new_id,
          exit_edge_id = new_id,
          direct_edge_id = new_id
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
           , NEW.$links_table_output_field
           , depth + 1
          FROM $closure_table_name
          WHERE $closure_table_child_field = NEW.$links_table_input_field;

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
          , NEW.$links_table_input_field
          , $closure_table_child_field
          , depth + 1
          FROM $closure_table_name
          WHERE $closure_table_parent_field = NEW.$links_table_output_field;

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
        WHERE A.$closure_table_child_field = NEW.$links_table_input_field
          AND B.$closure_table_parent_field = NEW.$links_table_output_field;

      #COMMIT ;

  #CALL `aiidadb`.`update_tc` ('INSERT', NEW.$links_table_input_field, NEW.$links_table_output_field, -1, -1);

END;

""")
    return trigger_update.substitute(links_table_name=links_table_name,
                                     links_table_input_field=links_table_input_field,
                                     links_table_output_field=links_table_output_field,
                                     closure_table_name=closure_table_name,
                                     closure_table_parent_field=closure_table_parent_field,
                                     closure_table_child_field=closure_table_child_field)


def get_mysql_trigger_delete(db_name,
                             links_table_name,
                             links_table_input_field,
                             links_table_output_field,
                             closure_table_name,
                             closure_table_parent_field,
                             closure_table_child_field):
    from string import Template

    trigger_delete = Template("""
    
CREATE TRIGGER update_tc_delete AFTER DELETE ON $links_table_name
FOR EACH ROW
proc_label:BEGIN

      DECLARE num_rows integer;

      IF NOT ( SELECT 1=1 FROM $closure_table_name
           WHERE $closure_table_parent_field = OLD.$links_table_input_field
           AND $closure_table_child_field = OLD.$links_table_output_field AND
           depth = 0 )
      THEN
        LEAVE proc_label;
      END IF;
      
      DELETE FROM PurgeList where 1 = 1;
      
      INSERT INTO PurgeList
        SELECT id FROM $closure_table_name
        WHERE $closure_table_parent_field = OLD.$links_table_input_field
        AND $closure_table_child_field = OLD.$links_table_output_field AND
        depth = 0;

      purge_loop: WHILE (1 = 1) DO

        INSERT INTO PurgeList
          SELECT id FROM $closure_table_name
            WHERE depth > 0
            AND ( entry_edge_id IN ( SELECT Id FROM PurgeList )
            OR direct_edge_id IN ( SELECT Id FROM PurgeList )
            OR exit_edge_id IN ( SELECT Id FROM PurgeList ) )
            AND Id NOT IN (SELECT Id FROM PurgeList );

        SET num_rows = ROW_COUNT();

        if (num_rows = 0) THEN
          LEAVE purge_loop;
        END IF;

      END WHILE;

      DELETE FROM $closure_table_name WHERE Id IN ( SELECT Id FROM PurgeList);


END;
""")
    return trigger_delete.substitute(links_table_name=links_table_name,
                                     links_table_input_field=links_table_input_field,
                                     links_table_output_field=links_table_output_field,
                                     closure_table_name=closure_table_name,
                                     closure_table_parent_field=closure_table_parent_field,
                                     closure_table_child_field=closure_table_child_field)


#====================================
#   Installer
#====================================

def install_tc(sender, **kwargs):
    from django.db import connection, transaction

    cursor = connection.cursor()

    links_table_name = "db_dblink"
    links_table_input_field = "input_id"
    links_table_output_field = "output_id"
    closure_table_name = "db_dbpath"
    closure_table_parent_field = "parent_id"
    closure_table_child_field = "child_id"

    if "mysql" in settings.DATABASES['default']['ENGINE']:

        import MySQLdb
        import warnings

        warnings.filterwarnings("ignore", "PROCEDURE.*")

        print '== Mysql found, installing transitive closure engine =='

        #         print get_mysql_tc(settings.DATABASES['default']['NAME'], links_table_name, links_table_input_field, links_table_output_field,
        #                                  closure_table_name, closure_table_parent_field, closure_table_child_field)
        db_name = settings.DATABASES['default']['NAME']

        print "Cleaning old triggers"
        try:
            cursor.execute("DROP PROCEDURE IF EXISTS `" + db_name + "`.`update_tc`;")
        except MySQLdb.Warning:
            pass
        try:
            cursor.execute("DROP TRIGGER IF EXISTS update_tc_insert;")
        except MySQLdb.Warning:
            pass

        try:
            cursor.execute("DROP TRIGGER IF EXISTS update_tc_delete;")
        except MySQLdb.Warning:
            pass

        try:
            cursor.execute("DROP TABLE IF EXISTS PurgeList;")
        except MySQLdb.Warning:
            pass

        cursor.execute("CREATE TABLE PurgeList (Id int);")

        print "Installing trigger for update"
        cursor.execute(
            get_mysql_trigger_update(db_name, links_table_name, links_table_input_field, links_table_output_field,
                                     closure_table_name, closure_table_parent_field, closure_table_child_field))
        transaction.commit_unless_managed()

        print "Installing trigger for delete"
        cursor = connection.cursor()
        cursor.execute(
            get_mysql_trigger_delete(db_name, links_table_name, links_table_input_field, links_table_output_field,
                                     closure_table_name, closure_table_parent_field, closure_table_child_field))

        transaction.commit_unless_managed()

    elif "postgresql" in settings.DATABASES['default']['ENGINE']:
        print '== Postgres found, installing transitive closure engine =='

        cursor.execute(get_pg_tc(links_table_name, links_table_input_field, links_table_output_field,
                                 closure_table_name, closure_table_parent_field, closure_table_child_field))

        transaction.commit_unless_managed()
    else:
        print '== No transitive closure installed =='

## dispatch_uid used to avoid to install twice the signal if this
## module is loaded twice (it happens e.g. when tests are run)
from django.db.models.signals import post_migrate
from django.apps import apps

post_migrate.connect(install_tc,
                     sender=apps.get_app_config('db'),
                     dispatch_uid="transitive_closure_post_migrate")
