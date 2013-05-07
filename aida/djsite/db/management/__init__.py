from django.db.models.signals import post_syncdb
from django.contrib.auth import models as auth_models
from django.conf import settings

def get_sqlite_tc_create_purgelist(links_table_name, 
              links_table_input_field, 
              links_table_output_field, 
              closure_table_name, 
              closure_table_parent_field, 
              closure_table_child_field):
    
    return """
CREATE TABLE purge_list (Id int);
"""

def get_sqlite_tc_create_trigger_update(links_table_name, 
              links_table_input_field, 
              links_table_output_field, 
              closure_table_name, 
              closure_table_parent_field, 
              closure_table_child_field):
    
    return """
CREATE TRIGGER update_tc INSERT ON """+links_table_name+"""
WHEN 
NOT EXISTS (
      SELECT Id FROM """+closure_table_name+""" 
      WHERE """+closure_table_parent_field+""" = new."""+links_table_input_field+"""
         AND """+closure_table_child_field+""" = new."""+links_table_output_field+"""
         AND depth = 0
         ) 
AND NOT new."""+links_table_input_field+""" = new."""+links_table_output_field+"""
AND NOT EXISTS (
      SELECT id FROM """+closure_table_name+""" 
        WHERE """+closure_table_parent_field+""" = new."""+links_table_output_field+""" 
        AND """+closure_table_child_field+""" = new."""+links_table_input_field+"""
        )

BEGIN

INSERT INTO """+closure_table_name+""" (
         """+closure_table_parent_field+""",
         """+closure_table_child_field+""",
         depth)
      VALUES (
         new."""+links_table_input_field+""",
         new."""+links_table_output_field+""",
         0);

    UPDATE """+closure_table_name+"""
      SET entry_edge_id = (SELECT id from """+closure_table_name+""" where """+closure_table_parent_field+"""=new."""+links_table_input_field+""" and """+closure_table_child_field+"""=new."""+links_table_output_field+""" and depth=0)
        , exit_edge_id = (SELECT id from """+closure_table_name+""" where """+closure_table_parent_field+"""=new."""+links_table_input_field+""" and """+closure_table_child_field+"""=new."""+links_table_output_field+""" and depth=0)
        , direct_edge_id = (SELECT id from """+closure_table_name+""" where """+closure_table_parent_field+"""=new."""+links_table_input_field+""" and """+closure_table_child_field+"""=new."""+links_table_output_field+""" and depth=0) 
      WHERE id = (SELECT id from """+closure_table_name+""" where """+closure_table_parent_field+"""=new."""+links_table_input_field+""" and """+closure_table_child_field+"""=new."""+links_table_output_field+""" and depth=0);

    INSERT INTO """+closure_table_name+""" (
      entry_edge_id,
      direct_edge_id,
      exit_edge_id,
      """+closure_table_parent_field+""",
      """+closure_table_child_field+""",
      depth) 
      SELECT id
         , (SELECT id from """+closure_table_name+""" where """+closure_table_parent_field+"""=new."""+links_table_input_field+""" and """+closure_table_child_field+"""=new."""+links_table_output_field+""" and depth=0)
         , (SELECT id from """+closure_table_name+""" where """+closure_table_parent_field+"""=new."""+links_table_input_field+""" and """+closure_table_child_field+"""=new."""+links_table_output_field+""" and depth=0)
         , """+closure_table_parent_field+""" 
         , new."""+links_table_output_field+"""
         , depth + 1
        FROM """+closure_table_name+"""
        WHERE """+closure_table_child_field+""" = new."""+links_table_input_field+""";

    INSERT INTO """+closure_table_name+""" (
      entry_edge_id,
      direct_edge_id,
      exit_edge_id,
      """+closure_table_parent_field+""",
      """+closure_table_child_field+""",
      depth)
      SELECT (SELECT id from """+closure_table_name+""" where """+closure_table_parent_field+"""=new."""+links_table_input_field+""" and """+closure_table_child_field+"""=new."""+links_table_output_field+""" and depth=0)
        , (SELECT id from """+closure_table_name+""" where """+closure_table_parent_field+"""=new."""+links_table_input_field+""" and """+closure_table_child_field+"""=new."""+links_table_output_field+""" and depth=0)
        , id 
        , new."""+links_table_input_field+"""
        , """+closure_table_child_field+"""
        , depth + 1
        FROM """+closure_table_name+"""
        WHERE """+closure_table_parent_field+""" = new."""+links_table_output_field+""";

    INSERT INTO """+closure_table_name+""" (
      entry_edge_id,
      direct_edge_id,
      exit_edge_id,
      """+closure_table_parent_field+""",
      """+closure_table_child_field+""",
      depth)
      SELECT A.id
        , (SELECT id from """+closure_table_name+""" where """+closure_table_parent_field+"""=new."""+links_table_input_field+""" and """+closure_table_child_field+"""=new."""+links_table_output_field+""" and depth=0)
        , B.id
        , A."""+closure_table_parent_field+"""
        , B."""+closure_table_child_field+"""
        , A.depth + B.depth + 2
     FROM """+closure_table_name+""" A
        CROSS JOIN """+closure_table_name+""" B
     WHERE A."""+closure_table_child_field+""" = new."""+links_table_input_field+"""
       AND B."""+closure_table_parent_field+""" = new."""+links_table_output_field+""";

END;
"""

def get_sqlite_tc_create_trigger_delete(links_table_name, 
              links_table_input_field, 
              links_table_output_field, 
              closure_table_name, 
              closure_table_parent_field, 
              closure_table_child_field):
    
    return """
CREATE TRIGGER deleted_from DELETE ON """+links_table_name+"""
WHEN 
EXISTS( 
  SELECT id FROM """+closure_table_name+"""
  WHERE """+closure_table_parent_field+""" = old."""+links_table_input_field+"""
  AND """+closure_table_child_field+""" = old."""+links_table_output_field+""" 
  AND depth = 0 )
BEGIN

INSERT INTO purge_list
      SELECT id FROM """+closure_table_name+"""
      WHERE """+closure_table_parent_field+""" = old."""+links_table_input_field+"""
      AND """+closure_table_child_field+""" = old."""+links_table_output_field+""" 
      AND depth = 0;

INSERT INTO purge_list
    SELECT id FROM """+closure_table_name+"""
    WHERE depth > 0
    AND ( entry_edge_id IN ( SELECT Id FROM purge_list ) 
    OR direct_edge_id IN ( SELECT Id FROM purge_list )
    OR exit_edge_id IN ( SELECT Id FROM purge_list ) )
    AND Id NOT IN (SELECT Id FROM purge_list );

DELETE FROM """+closure_table_name+""" WHERE Id IN ( SELECT Id FROM purge_list);

DELETE FROM purge_list;

END

"""

def get_sqlite_tc_create_trigger_loop(links_table_name, 
              links_table_input_field, 
              links_table_output_field, 
              closure_table_name, 
              closure_table_parent_field, 
              closure_table_child_field):
    
    return """
CREATE TRIGGER update_purgelist AFTER INSERT ON purge_list 
WHEN 
EXISTS( 
  SELECT id FROM """+closure_table_name+"""
    WHERE depth > 0
    AND ( entry_edge_id IN ( SELECT Id FROM purge_list ) 
    OR direct_edge_id IN ( SELECT Id FROM purge_list ) 
    OR exit_edge_id IN ( SELECT Id FROM purge_list ) )
    AND Id NOT IN (SELECT Id FROM purge_list )
) AND EXISTS (
  SELECT id FROM purge_list
)

BEGIN

  INSERT INTO purge_list
    SELECT id FROM """+closure_table_name+"""
    WHERE depth > 0
    AND ( entry_edge_id IN ( SELECT Id FROM purge_list ) 
    OR direct_edge_id IN ( SELECT Id FROM purge_list )
    OR exit_edge_id IN ( SELECT Id FROM purge_list ) )
    AND Id NOT IN (SELECT Id FROM purge_list );

END

"""

def get_pg_tc(links_table_name, 
              links_table_input_field, 
              links_table_output_field, 
              closure_table_name, 
              closure_table_parent_field, 
              closure_table_child_field):
    
    
      
    return """

DROP TRIGGER IF EXISTS autoupdate_tc ON """+links_table_name+""";
DROP FUNCTION IF EXISTS update_tc();

CREATE OR REPLACE FUNCTION update_tc()
  RETURNS trigger AS
$BODY$
DECLARE
     
    new_id INTEGER;
    old_id INTEGER;
    num_rows INTEGER;
    
BEGIN

  IF tg_op = 'INSERT' THEN

    IF EXISTS (
      SELECT Id FROM """+closure_table_name+""" 
      WHERE """+closure_table_parent_field+""" = new."""+links_table_input_field+"""
         AND """+closure_table_child_field+""" = new."""+links_table_output_field+"""
         AND depth = 0
         )
    THEN
      RETURN null;
    END IF;

    IF new."""+links_table_input_field+""" = new."""+links_table_output_field+"""
    OR EXISTS (
      SELECT id FROM """+closure_table_name+""" 
        WHERE """+closure_table_parent_field+""" = new."""+links_table_output_field+""" 
        AND """+closure_table_child_field+""" = new."""+links_table_input_field+"""
        )
    THEN
      RETURN null;
    END IF;

    INSERT INTO """+closure_table_name+""" (
         """+closure_table_parent_field+""",
         """+closure_table_child_field+""",
         depth)
      VALUES (
         new."""+links_table_input_field+""",
         new."""+links_table_output_field+""",
         0);
     
    new_id := lastval();

    UPDATE """+closure_table_name+"""
      SET entry_edge_id = new_id
        , exit_edge_id = new_id
        , direct_edge_id = new_id 
      WHERE id = new_id;





    INSERT INTO """+closure_table_name+""" (
      entry_edge_id,
      direct_edge_id,
      exit_edge_id,
      """+closure_table_parent_field+""",
      """+closure_table_child_field+""",
      depth) 
      SELECT id
         , new_id
         , new_id
         , """+closure_table_parent_field+""" 
         , new."""+links_table_output_field+"""
         , depth + 1
        FROM """+closure_table_name+"""
        WHERE """+closure_table_child_field+""" = new."""+links_table_input_field+""";




     
    INSERT INTO """+closure_table_name+""" (
      entry_edge_id,
      direct_edge_id,
      exit_edge_id,
      """+closure_table_parent_field+""",
      """+closure_table_child_field+""",
      depth)
      SELECT new_id
        , new_id
        , id 
        , new."""+links_table_input_field+"""
        , """+closure_table_child_field+"""
        , depth + 1
        FROM """+closure_table_name+"""
        WHERE """+closure_table_parent_field+""" = new."""+links_table_output_field+""";

    INSERT INTO """+closure_table_name+""" (
      entry_edge_id,
      direct_edge_id,
      exit_edge_id,
      """+closure_table_parent_field+""",
      """+closure_table_child_field+""",
      depth)
      SELECT A.id
        , new_id
        , B.id
        , A."""+closure_table_parent_field+"""
        , B."""+closure_table_child_field+"""
        , A.depth + B.depth + 2
     FROM """+closure_table_name+""" A
        CROSS JOIN """+closure_table_name+""" B
     WHERE A."""+closure_table_child_field+""" = new."""+links_table_input_field+"""
       AND B."""+closure_table_parent_field+""" = new."""+links_table_output_field+""";
   
  END IF;

  IF tg_op = 'DELETE' THEN

    IF NOT EXISTS( 
        SELECT id FROM """+closure_table_name+""" 
        WHERE """+closure_table_parent_field+""" = old."""+links_table_input_field+"""
        AND """+closure_table_child_field+""" = old."""+links_table_output_field+""" AND
        depth = 0 )
    THEN
        RETURN NULL;
    END IF;

    CREATE TABLE PurgeList (Id int);

    INSERT INTO PurgeList
      SELECT id FROM """+closure_table_name+"""
          WHERE """+closure_table_parent_field+""" = old."""+links_table_input_field+"""
        AND """+closure_table_child_field+""" = old."""+links_table_output_field+""" AND
        depth = 0;
          
    WHILE (1 = 1)
    loop
    
      INSERT INTO PurgeList
        SELECT id FROM """+closure_table_name+"""
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
    
    DELETE FROM """+closure_table_name+""" WHERE Id IN ( SELECT Id FROM PurgeList);
    DROP TABLE PurgeList;
    
  END IF;

  RETURN NULL;
  
END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;


CREATE TRIGGER autoupdate_tc
  AFTER INSERT OR DELETE OR UPDATE
  ON """+links_table_name+""" FOR each ROW
  EXECUTE PROCEDURE update_tc();

"""
    

def install_tc(sender, **kwargs):

    from django.db import connection, transaction
    cursor = connection.cursor()

    links_table_name = "db_link";
    links_table_input_field = "input_id"
    links_table_output_field = "output_id"
    closure_table_name = "db_path";
    closure_table_parent_field = "parent_id";
    closure_table_child_field = "child_id";
      
    if "postgresql" in settings.DATABASES['default']['ENGINE']:
      print '== Postegres found, installing transitive closure engine =='
      
      cursor.execute(get_pg_tc(links_table_name, links_table_input_field, links_table_output_field, 
              closure_table_name, closure_table_parent_field, closure_table_child_field))

      transaction.commit_unless_managed()

    elif "sqlite3" in settings.DATABASES['default']['ENGINE']:
      print '== SQLite3 found, installing transitive closure engine =='
      
      cursor.execute("DROP TABLE IF EXISTS purge_list;");
      cursor.execute(get_sqlite_tc_create_purgelist(links_table_name, links_table_input_field, links_table_output_field, 
              closure_table_name, closure_table_parent_field, closure_table_child_field))
      
      cursor.execute("DROP TRIGGER IF EXISTS update_tc;");
      cursor.execute(get_sqlite_tc_create_trigger_update(links_table_name, links_table_input_field, links_table_output_field, 
              closure_table_name, closure_table_parent_field, closure_table_child_field))
      
      cursor.execute("DROP TRIGGER IF EXISTS deleted_from;");
      cursor.execute(get_sqlite_tc_create_trigger_delete(links_table_name, links_table_input_field, links_table_output_field, 
              closure_table_name, closure_table_parent_field, closure_table_child_field))
      
      cursor.execute("DROP TRIGGER IF EXISTS purge_list.update_purgelist;");
      cursor.execute(get_sqlite_tc_create_trigger_loop(links_table_name, links_table_input_field, links_table_output_field, 
              closure_table_name, closure_table_parent_field, closure_table_child_field))
      
      transaction.commit_unless_managed()

    
    else:
      print '== No transitive closure installed =='

post_syncdb.connect(install_tc, sender=auth_models)
