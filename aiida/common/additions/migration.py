import getpass
import os

from aiida.common.setup import (AIIDA_CONFIG_FOLDER, DAEMON_SUBDIR, LOG_DIR)
from aiida.common.setup import (aiidadb_backend_key,
                                aiidadb_backend_value_django)
from aiida.common.setup import (get_config, store_config, install_daemon_files,
                                backup_config)

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Spyros Zoupanos"


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
        conf = get_config()

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
                if aiidadb_backend_key not in curr_profile.keys():
                    curr_profile[aiidadb_backend_key] = \
                        aiidadb_backend_value_django

        # Returning the configuration
        return conf

    def main_method(self):
        # Backup the previous config
        backup_config()
        # Get the AiiDA directory path
        aiida_directory = os.path.expanduser(AIIDA_CONFIG_FOLDER)
        # Construct the daemon directory path
        daemon_dir = os.path.join(aiida_directory, DAEMON_SUBDIR)
        # Construct the log directory path
        log_dir = os.path.join(aiida_directory, LOG_DIR)
        # Update the configuration if needed
        confs = self.adding_backend()
        # Store the configuration
        store_config(confs)
        # Update the daemon directory
        install_daemon_files(aiida_directory, daemon_dir, log_dir,
                             getpass.getuser())

if __name__ == '__main__':
    Migration().main_method()