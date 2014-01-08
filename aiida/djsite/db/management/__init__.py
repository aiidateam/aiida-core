## When using south, one must attach to the south post_migrate signal,
## because since the tables are managed by South, after the post_sync
## the tables are not created yet.
#from django.db.models.signals import post_syncdb
#from south.signals import post_migrate
## Actually, now we have a variable in settings that points to the correct
## signal.
from aiida.djsite.utils import get_after_database_creation_signal
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

def get_sqlite_tc_create_trigger_delete_NEW(links_table_name, 
              links_table_input_field, 
              links_table_output_field, 
              closure_table_name, 
              closure_table_parent_field, 
              closure_table_child_field):
    
    return """
CREATE TRIGGER deleted_from DELETE ON """+links_table_name+"""
BEGIN

DELETE FROM """+closure_table_name+""" WHERE Id IN (
      SELECT id FROM """+closure_table_name+"""
      WHERE """+closure_table_parent_field+""" = old."""+links_table_input_field+"""
      AND """+closure_table_child_field+""" = old."""+links_table_output_field+""" 
      AND depth = 0);

END
"""

def get_sqlite_tc_create_trigger_loop_NEW(links_table_name, 
              links_table_input_field, 
              links_table_output_field, 
              closure_table_name, 
              closure_table_parent_field, 
              closure_table_child_field):
    
    return """
CREATE TRIGGER path_delete_recursive DELETE ON """+closure_table_name+""" 
WHEN 
EXISTS( 
      SELECT id FROM """+closure_table_name+"""
    WHERE (entry_edge_id = old.id 
    OR direct_edge_id = old.id
    OR exit_edge_id = old.id)
    AND (id <> old.id))

BEGIN
  DELETE FROM """+closure_table_name+""" WHERE Id IN (
    SELECT id FROM """+closure_table_name+"""
    WHERE (entry_edge_id = old.id 
    OR direct_edge_id = old.id
    OR exit_edge_id = old.id)
    AND (id <> old.id));

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

    links_table_name = "db_link"
    links_table_input_field = "input_id"
    links_table_output_field = "output_id"
    closure_table_name = "db_path"
    closure_table_parent_field = "parent_id"
    closure_table_child_field = "child_id"
      
    if "postgresql" in settings.DATABASES['default']['ENGINE']:
        print '== Postegres found, installing transitive closure engine =='
      
        cursor.execute(get_pg_tc(links_table_name, links_table_input_field, links_table_output_field, 
                                 closure_table_name, closure_table_parent_field, closure_table_child_field))

        transaction.commit_unless_managed()
    elif "sqlite3" in settings.DATABASES['default']['ENGINE']:
        print '== SQLite3 found, installing transitive closure engine =='        
        # Use the new trigger without the support purge_list table
        
        from django.db.backends.sqlite3.base import Database as DjDatabase
        sqlite_version = DjDatabase.sqlite_version_info
        sqlite_version_string = DjDatabase.sqlite_version
        # This is the first version that supports recursive triggers
        if sqlite_version < (3, 6, 18):
            new_sql_trigger = False
            print r'   ||  NOTE: using old version of SQLite triggers  ||'
            print r'   ||  because your sqlite version is too old:     ||'
            print r'   \\  {} //'.format(
                (sqlite_version_string + ' (< 3.6.18)').ljust(43))
        else:
            new_sql_trigger = True
            print r'   ||  NOTE: using new version of SQLite triggers  ||'
            print r'   ||  because your sqlite version is sufficiently ||'
            print r'   \\  recent: {} //'.format(
                (sqlite_version_string + ' (> 3.6.18)').ljust(35))
        
        cursor.execute("DROP TRIGGER IF EXISTS update_tc;")
        cursor.execute(get_sqlite_tc_create_trigger_update(links_table_name, links_table_input_field, links_table_output_field, 
                                                           closure_table_name, closure_table_parent_field, closure_table_child_field))

        if new_sql_trigger:
            # the 'new' triggers work only if recursive triggers are active
            # This is required for sqlite >= 3.6.18; it is the default
            # from sqlite >=3.7
            # NOTE: The default maximum trigger recursion depth is 1000.
            # Hopefully, it is ok...
            # To change, set the SQLITE_MAX_TRIGGER_DEPTH variable.
            cursor.execute("PRAGMA RECURSIVE_TRIGGERS=true;")
            
            cursor.execute("DROP TABLE IF EXISTS purge_list;")
                        
            cursor.execute("DROP TRIGGER IF EXISTS deleted_from;")
            cursor.execute(get_sqlite_tc_create_trigger_delete_NEW(links_table_name, links_table_input_field, links_table_output_field, 
                                                                   closure_table_name, closure_table_parent_field, closure_table_child_field))

            cursor.execute("DROP TRIGGER IF EXISTS purge_list.update_purgelist;")
            cursor.execute("DROP TRIGGER IF EXISTS path_delete_recursive;")
            cursor.execute(get_sqlite_tc_create_trigger_loop_NEW(links_table_name, links_table_input_field, links_table_output_field, 
                                                                 closure_table_name, closure_table_parent_field, closure_table_child_field))
            
            transaction.commit_unless_managed()
        else:
            cursor.execute("DROP TABLE IF EXISTS purge_list;")
            cursor.execute(get_sqlite_tc_create_purgelist(links_table_name, links_table_input_field, links_table_output_field, 
                                                          closure_table_name, closure_table_parent_field, closure_table_child_field))
                  
            cursor.execute("DROP TRIGGER IF EXISTS deleted_from;")
            cursor.execute(get_sqlite_tc_create_trigger_delete(links_table_name, links_table_input_field, links_table_output_field, 
                                                               closure_table_name, closure_table_parent_field, closure_table_child_field))
      
            cursor.execute("DROP TRIGGER IF EXISTS purge_list.update_purgelist;")
            cursor.execute("DROP TRIGGER IF EXISTS path_delete_recursive;")
            cursor.execute(get_sqlite_tc_create_trigger_loop(links_table_name, links_table_input_field, links_table_output_field, 
                                                             closure_table_name, closure_table_parent_field, closure_table_child_field))
      
            transaction.commit_unless_managed()
    else:
        print '== No transitive closure installed =='

## dispatch_uid used to avoid to install twice the signal if this
## module is loaded twice (it happens e.g. when tests are run)
## Note: since we use south, we attach to post_migrate rather than to
## post_syncdb (see comment at the top of this file). But in tests,
## we have to attach to post_syncdb. Therefore, we use the
## utility function to get the proper signal
signal, sender = get_after_database_creation_signal() 
signal.connect(install_tc, sender=sender,
    dispatch_uid="transitive_closure_post_syncdb")
