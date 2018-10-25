#!/bin/bash
set -ev

# Needed on Jenkins
if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi

if [[ "$TEST_TYPE" != "pre-commit" ]]
    # no setup at all required for pre-commit to run
then
    # Here I create the actual DB for submission
    psql -h localhost -c "CREATE DATABASE $TEST_AIIDA_BACKEND ENCODING \"UTF8\" LC_COLLATE=\"en_US.UTF-8\" LC_CTYPE=\"en_US.UTF-8\" TEMPLATE=template0;" -U postgres -w

    # Here I create the test DB
    psql -h localhost -c "CREATE DATABASE test_$TEST_AIIDA_BACKEND ENCODING \"UTF8\" LC_COLLATE=\"en_US.UTF-8\" LC_CTYPE=\"en_US.UTF-8\" TEMPLATE=template0;" -U postgres -w

    # Here I setup the actual AiiDA profile, non-interactively
    verdi setup --non-interactive --backend=$TEST_AIIDA_BACKEND --email="aiida@localhost" --db-host="localhost" --db-port=5432 --db-name="$TEST_AIIDA_BACKEND" --db-username=postgres --db-password='' --repository="/tmp/repository_${TEST_AIIDA_BACKEND}/" --first-name=AiiDA --last-name=test --institution="AiiDA Team" $TEST_AIIDA_BACKEND

    # Here I setup the test AiiDA profile, non-interactively
    verdi setup --non-interactive --backend=$TEST_AIIDA_BACKEND --email="aiida@localhost" --db-host="localhost" --db-port=5432 --db-name="test_$TEST_AIIDA_BACKEND" --db-username=postgres --db-password='' --repository="/tmp/test_repository_test_${TEST_AIIDA_BACKEND}/" --first-name=AiiDA --last-name=test --institution="AiiDA Team" test_$TEST_AIIDA_BACKEND

    # Maybe not needed, but set this profile to be the default one
    verdi profile setdefault $TEST_AIIDA_BACKEND
fi
