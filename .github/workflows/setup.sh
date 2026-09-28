#!/usr/bin/env bash
set -ev

# Setup SSH on localhost
${GITHUB_WORKSPACE}/.github/workflows/setup_ssh.sh

# Replace the placeholders in configuration files with actual values
CONFIG="${GITHUB_WORKSPACE}/.github/config"
cp "${CONFIG}/slurm_rsa" "${HOME}/.ssh/slurm_rsa"

# Define the `slurm-ssh` host used by the SSH transport. The connection details are no
# longer stored in the computer's `auth_params`; the transport takes them from `~/.ssh/config`.
# Only this script sets up the slurm computer, so only it needs the host: the jobs that merely
# call `setup_ssh.sh` do not run the slurm service container.
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

sed -i "s|PLACEHOLDER_WORK_DIR|${GITHUB_WORKSPACE}|" "${CONFIG}/localhost.yaml"
sed -i "s|PLACEHOLDER_REMOTE_ABS_PATH_DOUBLER|${CONFIG}/doubler.sh|" "${CONFIG}/doubler.yaml"

verdi setup --non-interactive --config "${CONFIG}/profile.yaml"

# set up localhost computer
verdi computer setup --non-interactive --config "${CONFIG}/localhost.yaml"
verdi computer test localhost
verdi code create core.code.installed --non-interactive --config "${CONFIG}/doubler.yaml"
verdi code create core.code.installed --non-interactive --config "${CONFIG}/add.yaml"
verdi code create core.code.containerized --non-interactive --config "${CONFIG}/add-containerized.yaml"

# set up slurm-ssh computer
verdi computer setup --non-interactive --config "${CONFIG}/slurm-ssh.yaml"
verdi computer test slurm-ssh --print-traceback

verdi profile setdefault test_aiida
verdi config set runner.poll.interval 0
verdi config set warnings.development_version False
verdi config set warnings.rabbitmq_version False
