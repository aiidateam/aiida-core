#!/usr/bin/env bash
set -ev

# Setup SSH on localhost
${GITHUB_WORKSPACE}/.github/workflows/setup_ssh.sh

# Replace the placeholders in configuration files with actual values
CONFIG="${GITHUB_WORKSPACE}/.github/config"
cp "${CONFIG}/slurm_rsa" "${HOME}/.ssh/slurm_rsa"
sed -i "s|PLACEHOLDER_WORK_DIR|${GITHUB_WORKSPACE}|" "${CONFIG}/localhost.yaml"
sed -i "s|PLACEHOLDER_REMOTE_ABS_PATH_DOUBLER|${CONFIG}/doubler.sh|" "${CONFIG}/doubler.yaml"
sed -i "s|PLACEHOLDER_SSH_KEY|${HOME}/.ssh/slurm_rsa|" "${CONFIG}/slurm-ssh-config.yaml"

verdi setup --non-interactive --config "${CONFIG}/profile.yaml"

# set up localhost computer
verdi computer setup --non-interactive --config "${CONFIG}/localhost.yaml"
verdi computer configure core.local localhost --config "${CONFIG}/localhost-config.yaml"
verdi computer test localhost
verdi code create core.code.installed --non-interactive --config "${CONFIG}/doubler.yaml"
verdi code create core.code.installed --non-interactive --config "${CONFIG}/add.yaml"
verdi code create core.code.containerized --non-interactive --config "${CONFIG}/add-containerized.yaml"

# set up slurm-ssh computer
verdi computer setup --non-interactive --config "${CONFIG}/slurm-ssh.yaml"
verdi computer configure core.ssh slurm-ssh --non-interactive --config "${CONFIG}/slurm-ssh-config.yaml" -n  # needs slurm container
verdi computer test slurm-ssh --print-traceback

verdi profile setdefault test_aiida
verdi config set runner.poll.interval 0
verdi config set warnings.development_version False
verdi config set warnings.rabbitmq_version False
