#!/usr/bin/env bash
set -ev

ssh-keygen -q -t rsa -b 4096 -N "" -f "${HOME}/.ssh/id_rsa"
ssh-keygen -y -f "${HOME}/.ssh/id_rsa" >> "${HOME}/.ssh/authorized_keys"
ssh-keyscan -H localhost >> "${HOME}/.ssh/known_hosts"

# The permissions on the GitHub runner are 777 which will cause SSH to refuse the keys and cause authentication to fail
chmod 755 "${HOME}"

# Replace the placeholders in configuration files with actual values
CONFIG="${GITHUB_WORKSPACE}/.github/config"
sed -i "s|PLACEHOLDER_BACKEND|${AIIDA_TEST_BACKEND}|" "${CONFIG}/profile.yaml"
sed -i "s|PLACEHOLDER_PROFILE|test_${AIIDA_TEST_BACKEND}|" "${CONFIG}/profile.yaml"
sed -i "s|PLACEHOLDER_DATABASE_NAME|test_${AIIDA_TEST_BACKEND}|" "${CONFIG}/profile.yaml"
sed -i "s|PLACEHOLDER_REPOSITORY|/tmp/test_repository_test_${AIIDA_TEST_BACKEND}/|" "${CONFIG}/profile.yaml"
sed -i "s|PLACEHOLDER_WORK_DIR|${GITHUB_WORKSPACE}|" "${CONFIG}/localhost.yaml"
sed -i "s|PLACEHOLDER_REMOTE_ABS_PATH_DOUBLER|${CONFIG}/doubler.sh|" "${CONFIG}/doubler.yaml"

verdi setup --config "${CONFIG}/profile.yaml"
verdi computer setup --config "${CONFIG}/localhost.yaml"
verdi computer configure local localhost --config "${CONFIG}/localhost-config.yaml"
verdi code setup --config "${CONFIG}/doubler.yaml"
verdi code setup --config "${CONFIG}/add.yaml"

verdi profile setdefault test_${AIIDA_TEST_BACKEND}
verdi config runner.poll.interval 0
