from django.db.models.signals import post_syncdb
from django.contrib.auth import models as auth_models
from django.conf import settings

def install_tc(sender, **kwargs):
    
    from django.db import connection, transaction
    cursor = connection.cursor()
    
    # Data modifying operation - commit required
    if "postgresql" in settings.DATABASES['default']['ENGINE']:
      print '== Postegres found, installing transitive closure engine =='

      cursor.execute("""
DROP TRIGGER IF EXISTS autoupdate_tc ON scaling_datacalc_children;
DROP FUNCTION IF EXISTS update_tc();

CREATE FUNCTION update_tc() RETURNS trigger AS '
DECLARE
     
    new_id INTEGER;
    old_id INTEGER;
    
BEGIN

  IF tg_op = ''INSERT'' THEN

    IF EXISTS (
      SELECT Id FROM scaling_closure 
      WHERE start_datacalc_id = new.from_datacalc_id
	     AND end_datacalc_id = new.to_datacalc_id
	     AND hops = 0
	     )
    THEN
      RETURN null;
    END IF;

    IF new.from_datacalc_id = new.to_datacalc_id
    OR EXISTS (
      SELECT id FROM scaling_closure 
        WHERE start_datacalc_id = new.to_datacalc_id 
        AND end_datacalc_id = new.from_datacalc_id
        )
    THEN
      RETURN null;
    END IF;

    INSERT INTO scaling_closure (
         start_datacalc_id,
         end_datacalc_id,
         hops,
         source)
      VALUES (
         new.from_datacalc_id,
         new.to_datacalc_id,
         0,
         TG_TABLE_NAME);
     
    new_id := lastval();

    UPDATE scaling_closure
      SET entry_edge_id = new_id
        , exit_edge_id = new_id
        , direct_edge_id = new_id 
      WHERE id = new_id;





    INSERT INTO scaling_closure (
      entry_edge_id,
      direct_edge_id,
      exit_edge_id,
      start_datacalc_id,
      end_datacalc_id,
      hops,
      source) 
      SELECT id
         , new_id
         , new_id
         , start_datacalc_id 
         , new.to_datacalc_id
         , hops + 1
         , TG_TABLE_NAME
        FROM scaling_closure
        WHERE end_datacalc_id = new.from_datacalc_id;




     
    INSERT INTO scaling_closure (
      entry_edge_id,
      direct_edge_id,
      exit_edge_id,
      start_datacalc_id,
      end_datacalc_id,
      hops,
      source)
      SELECT new_id
        , new_id
        , exit_edge_id 
        , new.from_datacalc_id
        , end_datacalc_id
        , hops + 1
        , TG_TABLE_NAME
        FROM scaling_closure
        WHERE start_datacalc_id = new.to_datacalc_id;

    INSERT INTO scaling_closure (
      entry_edge_id,
      direct_edge_id,
      exit_edge_id,
      start_datacalc_id,
      end_datacalc_id,
      hops,
      source)
      SELECT A.entry_edge_id
        , new_id
        , B.exit_edge_id
        , A.start_datacalc_id
        , B.end_datacalc_id
        , A.hops + B.hops + 2
        , TG_TABLE_NAME
     FROM scaling_closure A
        CROSS JOIN scaling_closure B
     WHERE A.end_datacalc_id = new.from_datacalc_id
       AND B.start_datacalc_id = new.to_datacalc_id;

    return new;
    
  END IF;
  
END
' LANGUAGE plpgsql;


CREATE TRIGGER autoupdate_tc 
  AFTER INSERT OR DELETE OR UPDATE
  ON scaling_datacalc_children FOR each ROW
  EXECUTE PROCEDURE update_tc();
""")
    
      transaction.commit_unless_managed()
    else:
      print '== No transitive closure installed =='

post_syncdb.connect(install_tc, sender=auth_models)

