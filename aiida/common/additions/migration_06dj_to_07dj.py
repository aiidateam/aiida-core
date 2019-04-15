#!/usr/bin/env python
# -*- coding: utf-8 -*-
import getpass
import os

import aiida.common.setup as setup

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1.1"
__authors__ = "The AiiDA team."


class Migration(object):
    """
    This class converts the configuration from the AiiDA 0.6.0 version (Django)
    to version 0.7.0 (Django).

    It is assumed that it is already (correctly) defined the place that the
    various configuration files are found in the aiida.common.setup.
    """

    # Profile key
    _profiles_key = "profiles"

    def perform_migration(self):
        # Backup the previous config
        setup.backup_config()
        # Get the AiiDA directory path
        aiida_directory = os.path.expanduser(setup.AIIDA_CONFIG_FOLDER)
        # Construct the daemon directory path
        daemon_dir = os.path.join(aiida_directory, setup.DAEMON_SUBDIR)
        # Construct the log directory path
        log_dir = os.path.join(aiida_directory, setup.LOG_SUBDIR)
        # Update the daemon directory
        setup.install_daemon_files(aiida_directory, daemon_dir, log_dir,
                             getpass.getuser())

if __name__ == '__main__':
    Migration().perform_migration()
    print("Migration finished.")
