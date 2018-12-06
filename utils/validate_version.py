"""Check that version numbers match.

Check version number in setup.json and aiida_core/__init__.py and make sure
they match.
"""
from __future__ import absolute_import
from __future__ import print_function
import os
import json
import sys

THIS_PATH = os.path.split(os.path.realpath(__file__))[0]

# Get content of setup.json
SETUP_FNAME = 'setup.json'
SETUP_PATH = os.path.join(THIS_PATH, os.pardir, SETUP_FNAME)
with open(SETUP_PATH) as f:
    setup_content = json.load(f)  # pylint: disable=invalid-name

# Get version from python package
sys.path.insert(0, os.path.join(THIS_PATH, os.pardir))
import aiida  # pylint: disable=wrong-import-position
VERSION = aiida.__version__

if VERSION != setup_content['version']:
    print("Version number mismatch detected:")
    print("Version number in '{}': {}".format(SETUP_FNAME, setup_content['version']))
    print("Version number in '{}/__init__.py': {}".format('aiida', VERSION))
    sys.exit(1)

# Overwrite version in setup.json
#setup_content['version'] = VERSION
#with open(SETUP_PATH, 'w') as f:
#	json.dump(setup_content, f, indent=2, sort_keys=True)
