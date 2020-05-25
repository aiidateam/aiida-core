#!/bin/bash

## Adapt the credentials here
AIIDAUSER=aiida
AIIDADB=aiidadb
AIIDAPORT=5432
## STORE THE PASSWORD, IN THE PROPER FORMAT, IN THE ~/.pgpass file
## see http://www.postgresql.org/docs/current/static/libpq-pgpass.html


# Change the destination location here
AIIDALOCALTMPDUMPFILE=~/.aiida/${AIIDADB}-backup.psql.gz
if [ -e ${AIIDALOCALTMPDUMPFILE} ]
then
    mv ${AIIDALOCALTMPDUMPFILE} ${AIIDALOCALTMPDUMPFILE}~
fi

# NOTE: password stored in ~/.pgpass, where pg_dump will read it automatically
pg_dump -h localhost -p $AIIDAPORT -U $AIIDAUSER $AIIDADB | gzip > $AIIDALOCALTMPDUMPFILE || rm $AIIDALOCALTMPDUMPFILE

## IMPORTANT!!
## MOVE THE FILE HERE TO A DIFFERENT FILESYSTEM, OR MAKE SURE THIS IS BACKED UP ON A DIFFERENT MACHINE!!
## (e.g. you can call `rsync`, `scp`, ...)
