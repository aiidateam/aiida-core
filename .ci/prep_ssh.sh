#!/bin/bash

# Be verbose, and stop with error as soon there's one
set -ev

# This is needed for the SSH tests (being able to ssh to localhost)
# And will also be used for the docker test.

# Make sure we don't overwrite an existing SSH key (seems to be the case for private Travis instances)
[ -f "${HOME}/.ssh/id_rsa" ] || ssh-keygen -q -t rsa -N "" -f "${HOME}/.ssh/id_rsa"

# Extract the public key directly from the private key without requiring .pub file (again: private Travis instances)
ssh-keygen -y -f "${HOME}/.ssh/id_rsa" >> "${HOME}/.ssh/authorized_keys"

# Register the current hosts fingerprint
ssh-keyscan -H localhost >> "${HOME}/.ssh/known_hosts"
