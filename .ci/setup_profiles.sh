#!/bin/bash
set -ev

# Needed on Jenkins
if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi

if [[ "$TEST_TYPE" == "tests" || "$TEST_TYPE" == "docs" ]]
then
    # Create the main database
    PSQL_COMMAND="CREATE DATABASE $AIIDA_TEST_BACKEND ENCODING \"UTF8\" LC_COLLATE=\"en_US.UTF-8\" LC_CTYPE=\"en_US.UTF-8\" TEMPLATE=template0;"
    psql -h localhost -c "${PSQL_COMMAND}" -U postgres -w

    # Create the test database
    PSQL_COMMAND="CREATE DATABASE test_$AIIDA_TEST_BACKEND ENCODING \"UTF8\" LC_COLLATE=\"en_US.UTF-8\" LC_CTYPE=\"en_US.UTF-8\" TEMPLATE=template0;"
    psql -h localhost -c "${PSQL_COMMAND}" -U postgres -w

    # Setup the main profile
    verdi setup --profile $AIIDA_TEST_BACKEND \
        --email="aiida@localhost" --first-name=AiiDA --last-name=test --institution="AiiDA Team" \
        --db-engine 'postgresql_psycopg2' --db-backend=$AIIDA_TEST_BACKEND --db-host="localhost" --db-port=5432 \
        --db-name="$AIIDA_TEST_BACKEND" --db-username=postgres --db-password='' \
        --repository="/tmp/repository_${AIIDA_TEST_BACKEND}/" --non-interactive

    # Setup the test profile
    verdi setup --profile test_$AIIDA_TEST_BACKEND \
        --email="aiida@localhost" --first-name=AiiDA --last-name=test --institution="AiiDA Team" \
        --db-engine 'postgresql_psycopg2' --db-backend=$AIIDA_TEST_BACKEND --db-host="localhost" --db-port=5432 \
        --db-name="test_$AIIDA_TEST_BACKEND" --db-username=postgres --db-password='' \
         --repository="/tmp/test_repository_test_${AIIDA_TEST_BACKEND}/" --non-interactive

    # Set the main profile as the default
    verdi profile setdefault $AIIDA_TEST_BACKEND

    # Set the polling interval to 0 otherwise the tests take too long
    verdi config runner.poll.interval 0
fi
