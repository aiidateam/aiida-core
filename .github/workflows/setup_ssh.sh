#!/usr/bin/env bash
# Sets up ssh keys to allow a ssh connection to localhost. This is needed
# because localhost is used as remote address to run the tests locally.
set -ev

mkdir -p ${PWD}/.ssh
mkdir -p ${HOME}/.ssh
ssh-keygen -q -t rsa -b 4096 -N "" -f "${PWD}/.ssh/id_rsa_aiida_pytest"
ssh-keygen -y -f "${PWD}/.ssh/id_rsa_aiida_pytest" >> "${HOME}/.ssh/authorized_keys"
# for the ssh_auto the tests still require the default key
ssh-keygen -q -t rsa -b 4096 -N "" -f "${HOME}/.ssh/id_rsa"
ssh-keygen -y -f "${HOME}/.ssh/id_rsa" >> "${HOME}/.ssh/authorized_keys"
ssh-keyscan -H localhost >> "${HOME}/.ssh/known_hosts"

# The permissions on the GitHub runner are 777 which will cause SSH to refuse the keys and cause authentication to fail
chmod 755 "${HOME}"
