#!/bin/bash
set -ev

# Needed on Jenkins
if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi

if [[ "$TEST_TYPE" != "pre-commit" ]]
    # no setup at all required for pre-commit to run
then
    # Here I create the actual DB for submission
    psql -h localhost -c "CREATE DATABASE $TEST_AIIDA_BACKEND;" -U postgres -w
    # Here I create the test DB
    psql -h localhost -c "CREATE DATABASE test_$TEST_AIIDA_BACKEND;" -U postgres -w

    # Here I setup the actual AiiDA profile, non-interactively
    verdi -p $TEST_AIIDA_BACKEND setup --non-interactive --backend=$TEST_AIIDA_BACKEND --email="aiida@localhost" --db_host="localhost" --db_port=5432 --db_name="$TEST_AIIDA_BACKEND" --db_user=postgres --db_pass='' --repo="/tmp/test_repository_${TEST_AIIDA_BACKEND}/" --first-name=AiiDA --last-name=test --institution="AiiDA Team" --no-password

    # Here I setup the test AiiDA profile, non-interactively
    verdi -p test_$TEST_AIIDA_BACKEND setup --non-interactive --backend=$TEST_AIIDA_BACKEND --email="aiida@localhost" --db_host="localhost" --db_port=5432 --db_name="test_$TEST_AIIDA_BACKEND" --db_user=postgres --db_pass='' --repo="/tmp/test_repository_test_${TEST_AIIDA_BACKEND}/" --first-name=AiiDA --last-name=test --institution="AiiDA Team" --no-password

    # Maybe not needed, but set this profile to be the default one
    verdi profile setdefault $TEST_AIIDA_BACKEND
fi
