import getpass
import os

from aiida.common.setup import (AIIDA_CONFIG_FOLDER, DAEMON_SUBDIR, LOG_DIR)
from aiida.common.setup import (aiidadb_backend_key,
                                aiidadb_backend_value_django)
from aiida.common.setup import (get_config, store_config, install_daemon_files)


class Migration(object):

    # Profile key
    _profiles_key = "profiles"

    def adding_backend(self):
        conf = get_config()
        print("Configuration {}".format(conf))
        print(type(conf).__name__)
        print("{}".format(conf.keys()))

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

    def install_deamon_file(self):
        pass

    def main_method(self):
        aiida_directory = os.path.expanduser(AIIDA_CONFIG_FOLDER)
        daemon_dir = os.path.join(aiida_directory, DAEMON_SUBDIR)
        log_dir = os.path.join(aiida_directory, LOG_DIR)

        # We update the configuration if needed
        confs = self.adding_backend()

        # We store the configuration
        store_config(confs)

        # We update the daemon directory
        install_daemon_files(aiida_directory, daemon_dir, log_dir,
                             getpass.getuser())

if __name__ == '__main__':
    Migration().main_method()