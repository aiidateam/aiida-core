#!/usr/bin/env bash
# Sets up ssh keys to allow a ssh connection to localhost. This is needed
# because localhost is used as remote address to run the tests locally.
set -ev

mkdir -p ${HOME}/.ssh
ssh-keygen -q -t rsa -b 4096 -N "" -f "${HOME}/.ssh/id_rsa_aiida_pytest"
ssh-keygen -y -f "${HOME}/.ssh/id_rsa_aiida_pytest" >> "${HOME}/.ssh/authorized_keys"
ssh-keyscan -H localhost >> "${HOME}/.ssh/known_hosts"
# to test core.ssh_auto transport plugin we need to append this to the config
cat <<EOT >> ${HOME}/.ssh/config
Host localhost
        IdentityFile ${HOME}/.ssh/id_rsa_aiida_pytest
EOT


# The permissions on the GitHub runner are 777 which will cause SSH to refuse the keys and cause authentication to fail
chmod 755 "${HOME}"
