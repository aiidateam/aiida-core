#!/usr/bin/env bash
# Configure a dedicated SSH identity for AiiDA's localhost transport tests.
#
# This intentionally never reads, replaces, or otherwise uses a developer's
# default SSH identities.
set -euo pipefail

readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly TEST_SSH_DIRECTORY="${PROJECT_ROOT}/.aiida-core-test-ssh"
readonly KEY_PATH="${TEST_SSH_DIRECTORY}/id_ed25519"
readonly PUBLIC_KEY_PATH="${KEY_PATH}.pub"
readonly KNOWN_HOSTS_PATH="${TEST_SSH_DIRECTORY}/known_hosts"
readonly SSH_CONFIG_PATH="${TEST_SSH_DIRECTORY}/config"
readonly AUTHORIZED_KEYS_PATH="${HOME}/.ssh/authorized_keys"

success() {
    if [[ "${key_existed}" == true ]]; then
        echo "Existing AiiDA test key was verified: it can connect to localhost."
    else
        echo "Created AiiDA test key and verified that it can connect to localhost."
    fi
    echo "Set AIIDA_CORE_TEST_ASYNC_SSH_CONFIG=${SSH_CONFIG_PATH} when running AsyncSSH tests."
}

mkdir -p "${TEST_SSH_DIRECTORY}"
chmod 700 "${TEST_SSH_DIRECTORY}"
mkdir -p "${HOME}/.ssh"
chmod 700 "${HOME}/.ssh"

if [[ -e "${KEY_PATH}" ]]; then
    key_existed=true
    if ! ssh-keygen -y -f "${KEY_PATH}" > "${PUBLIC_KEY_PATH}.tmp"; then
        echo "ERROR: existing AiiDA test key is not a valid private key: ${KEY_PATH}" >&2
        exit 1
    fi
    mv "${PUBLIC_KEY_PATH}.tmp" "${PUBLIC_KEY_PATH}"
else
    key_existed=false
    ssh-keygen -q -t ed25519 -N '' -f "${KEY_PATH}" -C 'aiida-core-test-suite'
fi
chmod 600 "${KEY_PATH}"
chmod 644 "${PUBLIC_KEY_PATH}"

touch "${AUTHORIZED_KEYS_PATH}"
chmod 600 "${AUTHORIZED_KEYS_PATH}"
if ! grep -qxF -- "$(<"${PUBLIC_KEY_PATH}")" "${AUTHORIZED_KEYS_PATH}"; then
    printf '%s\n' "$(<"${PUBLIC_KEY_PATH}")" >> "${AUTHORIZED_KEYS_PATH}"
fi

cat > "${SSH_CONFIG_PATH}" << EOF
Host localhost
    IdentityFile ${KEY_PATH}
    IdentitiesOnly yes
    UserKnownHostsFile ${KNOWN_HOSTS_PATH}
    GlobalKnownHostsFile /dev/null
    StrictHostKeyChecking yes
EOF
chmod 600 "${SSH_CONFIG_PATH}"

if [[ "${key_existed}" == true ]]; then
    if ssh -F "${SSH_CONFIG_PATH}" -o BatchMode=yes -o ConnectTimeout=5 localhost true; then
        success
        exit 0
    fi
    echo "WARNING: localhost could not yet be verified with the existing AiiDA test SSH key; refreshing its test host key." >&2
fi

ssh-keyscan -H localhost > "${KNOWN_HOSTS_PATH}.tmp"
mv "${KNOWN_HOSTS_PATH}.tmp" "${KNOWN_HOSTS_PATH}"
chmod 644 "${KNOWN_HOSTS_PATH}"

if ! ssh -F "${SSH_CONFIG_PATH}" -o BatchMode=yes -o ConnectTimeout=5 localhost true; then
    echo "ERROR: the AiiDA test SSH identity could not connect to localhost." >&2
    echo "Check that an SSH server is running and accepts ${PUBLIC_KEY_PATH}." >&2
    exit 1
fi

success
