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
    This class converts the configuration from the AiiDA version with one
    backend (Django) as it is described in commit e048939 to the implementation
    that supports DJango and SQLAlchemy.

    It is assumed that it is already (correctly) defined the place that the
    various configuration files are found in the aiida.common.setup.
    """

    # Profile key
    _profiles_key = "profiles"

    def adding_backend(self):
        """
        Gets the main AiiDA configuration and searches if there is a backend
        defined. If there isn't any then Django is added.
        """
        # Get the available configuration
        conf = setup.get_config()

        # Identifying all the available profiles
        if self._profiles_key in conf.keys():
            profiles = conf[self._profiles_key]
            p_keys = profiles.keys()
            # For every profile
            for p_key in p_keys:
                # get the
                curr_profile = profiles[p_key]

                # Check if there is a specific backend in the profile
                # and if not, add Django as backend
                if setup.aiidadb_backend_key not in curr_profile.keys():
                    curr_profile[setup.aiidadb_backend_key] = \
                        setup.aiidadb_backend_value_django

        # Returning the configuration
        return conf

    def perform_migration(self):
        # Backup the previous config
        setup.backup_config()
        # Get the AiiDA directory path
        aiida_directory = os.path.expanduser(setup.AIIDA_CONFIG_FOLDER)
        # Construct the daemon directory path
        daemon_dir = os.path.join(aiida_directory, setup.DAEMON_SUBDIR)
        # Construct the log directory path
        log_dir = os.path.join(aiida_directory, setup.LOG_SUBDIR)
        # Update the configuration if needed
        confs = self.adding_backend()
        # Store the configuration
        setup.store_config(confs)
        # Update the daemon directory
        setup.install_daemon_files(aiida_directory, daemon_dir, log_dir,
                             getpass.getuser())

if __name__ == '__main__':
    Migration().perform_migration()
    print("Migration finished.")
