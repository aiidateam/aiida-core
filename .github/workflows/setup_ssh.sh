#!/usr/bin/env bash
set -ev

ssh-keygen -q -t rsa -b 4096 -N "" -f "${HOME}/.ssh/id_rsa"
ssh-keygen -y -f "${HOME}/.ssh/id_rsa" >> "${HOME}/.ssh/authorized_keys"
ssh-keyscan -H localhost >> "${HOME}/.ssh/known_hosts"

# Define the `slurm-ssh` host used by the `core.ssh` transport. The connection details are no
# longer stored in the computer's `auth_params`; the transport takes them from `~/.ssh/config`.
cat >> "${HOME}/.ssh/config" <<EOF
Host slurm-ssh
    HostName localhost
    User xenon
    Port 5001
    IdentityFile ${HOME}/.ssh/slurm_rsa
EOF
chmod 600 "${HOME}/.ssh/config"

# The slurm service container listens on port 5001. Its host key has to be known upfront, since
# `asyncssh` does not implement `StrictHostKeyChecking=accept-new`. The container may still be
# booting, so retry until `sshd` answers.
SLURM_HOST_KEYS=''
for _ in $(seq 30); do
    SLURM_HOST_KEYS=$(ssh-keyscan -p 5001 localhost 2>/dev/null || true)
    if [ -n "${SLURM_HOST_KEYS}" ]; then
        break
    fi
    sleep 2
done
echo "${SLURM_HOST_KEYS}" >> "${HOME}/.ssh/known_hosts"
grep -q '^\[localhost\]:5001 ' "${HOME}/.ssh/known_hosts"

# The permissions on the GitHub runner are 777 which will cause SSH to refuse the keys and cause authentication to fail
chmod 755 "${HOME}"
