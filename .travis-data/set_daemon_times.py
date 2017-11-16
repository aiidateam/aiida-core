#!/usr/bin/env python
"""
For AiiDA 0.10.0, we set the times of the daemon
to 5 seconds.

.. note:: This needs to be removed (or adapted)
   if the daemon is modified to read the times
   from a different location, or the format of the config
   file is modified.
"""
import os
import sys
import shutil
import json

filename = os.path.expanduser("~/.aiida/config.json")

with open(filename) as f:
    profiles = json.load(f)

try:
    profile_name = sys.argv[1]
except IndexError:
    print >> sys.stderr, "Please pass a profile name on the command line"
    sys.exit(1)

for k, v in [
    ("DAEMON_INTERVALS_SUBMIT", 5),
    ("DAEMON_INTERVALS_UPDATE", 5),
    ("DAEMON_INTERVALS_RETRIEVE", 5),
    ]:
    profiles['profiles'][profile_name][k] = v

shutil.copy(filename, filename + "~")
with open(filename, 'w') as f:
    json.dump(profiles, f)

