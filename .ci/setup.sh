#!/usr/bin/env bash
set -ev

# The following is needed on jenkins, for some reason bashrc is not reloaded automatically
if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi

# Add the .ci and the polish folder to the python path such that defined workchains can be found by the daemon
export PYTHONPATH="${PYTHONPATH}:${WORKSPACE_PATH}/.ci"
export PYTHONPATH="${PYTHONPATH}:${WORKSPACE_PATH}/.ci/polish"

PSQL_COMMAND="CREATE DATABASE $AIIDA_TEST_BACKEND ENCODING \"UTF8\" LC_COLLATE=\"en_US.UTF-8\" LC_CTYPE=\"en_US.UTF-8\" TEMPLATE=template0;"
psql -h localhost -c "${PSQL_COMMAND}" -U postgres -w

verdi setup --profile $AIIDA_TEST_BACKEND \
    --email="aiida@localhost" --first-name=AiiDA --last-name=test --institution="AiiDA Team" \
    --db-engine 'postgresql_psycopg2' --db-backend=$AIIDA_TEST_BACKEND --db-host="localhost" --db-port=5432 \
    --db-name="$AIIDA_TEST_BACKEND" --db-username=postgres --db-password='' \
    --repository="/tmp/repository_${AIIDA_TEST_BACKEND}/" --non-interactive

verdi profile setdefault $AIIDA_TEST_BACKEND
verdi config runner.poll.interval 0

# Start the daemon for the correct profile and add four additional workers to prevent deadlock with integration tests
verdi -p $AIIDA_TEST_BACKEND daemon start
verdi -p $AIIDA_TEST_BACKEND daemon incr 4

verdi -p $AIIDA_TEST_BACKEND computer setup --non-interactive --label=localhost --hostname=localhost --transport=local \
    --scheduler=direct --mpiprocs-per-machine=1 --prepend-text="" --append-text=""
verdi -p $AIIDA_TEST_BACKEND computer configure local localhost --non-interactive --safe-interval=0

# Configure the 'add' code inside localhost
verdi -p $AIIDA_TEST_BACKEND code setup -n -L add \
    -D "simple script that adds two numbers" --on-computer -P arithmetic.add \
    -Y localhost --remote-abs-path=/usr/local/bin/add.sh
