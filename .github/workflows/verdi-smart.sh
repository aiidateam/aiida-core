#!/usr/bin/env bash

# Test whether the verdi-cli.json file is up to date with the newest changes.
# It runs the script `generate_verdi_cli_json.py` to generate a new file, then check a diff with a current existing file.
# If the diff is empty, it means that the file is up to date.
# If the diff is not empty, it means that the file is not up to date and needs to be updated.
# The script will exit with a non-zero code if the diff is not empty.


#!/bin/bash
# filepath: /home/khosra_a/development/repo/aiida-core/.github/workflows/verdi-smart.sh
# Test whether the verdi-cli.json file is up to date with the newest changes.
# It runs the script `generate_verdi_cli_json.py` to generate a new file, then check a diff with a current existing file.
# If the diff is empty, it means that the file is up to date.
# If the diff is not empty, it means that the file is not up to date and needs to be updated.
# The script will exit with a non-zero code if the diff is not empty.

set -e  # Exit immediately if a command exits with a non-zero status

# Define paths
REPO_ROOT="$(git rev-parse --show-toplevel)"
VERDI_CLI_JSON="${REPO_ROOT}/src/aiida/cmdline/commands/cmd_smart/utils/verdi_cli.json"
TEMP_JSON="/tmp/verdi_cli_temp.json"
GENERATOR_SCRIPT="${REPO_ROOT}/src/aiida/cmdline/commands/cmd_smart/utils/generate_verdi_cli_json.py"

echo "Checking if verdi-cli.json is up to date..."

mv "${VERDI_CLI_JSON}" "${TEMP_JSON}"

python "${GENERATOR_SCRIPT}"

# Compare the fresh version with the existing file
if diff -q "${VERDI_CLI_JSON}" "${TEMP_JSON}" > /dev/null; then
    echo "✅ verdi-cli.json is up to date!"
    exit 0
else
    echo "❌ verdi-cli.json is not up to date!"
    echo "Please run 'python ${GENERATOR_SCRIPT} -o ${VERDI_CLI_JSON}' to update it."
    echo "Diff between current and expected:"
    diff -u "${VERDI_CLI_JSON}" "${TEMP_JSON}" || true
    exit 1
fi
