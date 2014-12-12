Description of the Schema versions
(as defined in aiida.djsite.db.models.SCHEMA_VERSION)

** Version 1.0.1:
   Added the JobCalculation subclass of Calculation, and moved all plugins
   as subclasses of JobCalculation. Migration will convert all type strings
   from 'calculation.Calculation.' to 'calculation.job.JobCalculation.'
   and 'calculation.ANYTHINGELSE' to 'calculation.job.ANYTHINGELSE'.
   
** Version 1.0.0:
   Initial stable version of the DB schema
   
