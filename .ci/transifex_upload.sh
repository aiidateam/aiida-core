#!/bin/bash

# Be verbose, and stop with error as soon there's one
set -ev


pip install virtualenv
virtualenv ~/env
source ~/env/bin/activate
pip install transifex-client sphinx-intl
pip install ".[docs,testing]"

# Generate pot file and upload to transifex platform
TRANSIFEX_PROJECT_NAME="aiida-core"
export RUN_APIDOC="False"
export READTHEDOCS="True"
sphinx-build -b gettext docs/source locale
tx init --no-interactive
sphinx-intl update-txconfig-resources --pot-dir locale --transifex-project-name ${TRANSIFEX_PROJECT_NAME}
sudo echo $'[https://www.transifex.com]\nhostname = https://www.transifex.com\nusername = '"$TRANSIFEX_USER"$'\npassword = '"$TRANSIFEX_PASSWORD"$'\n' > ~/.transifexrc
tx push -s
